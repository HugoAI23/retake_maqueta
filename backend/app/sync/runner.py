"""Ejecutor de consultas de obtención (spec 003: RF-22, RF-43 a RF-47, RF-141 a RF-146; T-051).

Orquesta el flujo:
conector → ingesta → curación → avistamientos → registro → estado de la fuente → aviso de cambios.
"""

import uuid
from collections.abc import Callable, Collection
from dataclasses import replace
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curation.loader import Curation
from app.db.models import DatasetChange, SourceState
from app.ingest.pipeline import IngestReport, ingest_records
from app.ingest.sightings import apply_sightings, detect_disappearances
from app.sources import bp
from app.sources.contract import ConsultaResult
from app.sources.http import PoliteClient
from app.sync.notify import notify_changes
from app.sync.planner import PlannedQuery
from app.sync.registry import record_incident, record_run


# Consultas que listan todos los partidos de la temporada: son la base para reconocer una
# respuesta vacía (RF-46) y para decidir que un partido ha desaparecido (RF-50).
LISTING_JOBS = ("initial_load", "regular")


def consult(query: PlannedQuery, client: PoliteClient, now: datetime,
            known_guests: Collection[str] = ()) -> ConsultaResult:
    """Consulta del conector que corresponde a cada tipo de consulta del plan (§5).

    - Carga inicial y "Resto": listado completo; después, las fichas de cada equipo (`team_id`).
    - "Antes del partido" y la lista de "En vivo": solo la lista de próximos y en vivo.
    - Partido en vivo y revisión de un partido terminado: su página.

    `known_guests` son los equipos invitados que ya están en la base: el listado no vuelve a pedir su
    ficha, que va una vez al mes (RF-18b, plan I-38).
    """
    if query.team_id is not None:
        return bp.consult_teams(client, [query.team_id], query.season, now, job=query.job,
                                guests={query.team_id} if query.guest else ())
    if query.match_id is not None and query.job in ("live", "finished_matches"):
        return bp.consult_match(client, query.match_id, now, job=query.job)
    if query.job in ("pre_match", "live"):
        return bp.consult_upcoming(client, now, job=query.job, known_guests=known_guests)
    if query.job in LISTING_JOBS:
        return bp.consult_regular(client, now, job=query.job, known_guests=known_guests)
    raise ValueError(f"Consulta de conector no soportada: {query.job!r}")


def execute_consultation(
    session: Session,
    result: ConsultaResult,
    curation: Curation,
    now: datetime | None = None,
    started_at: datetime | None = None,
    request_id: uuid.UUID | None = None,
    logo_fetcher: Callable | None = None,
    notify_fn: Callable[[set[str]], None] | None = None,
    follow_up: bool = False,
) -> IngestReport:
    """Procesa el resultado de una consulta a una fuente y actualiza el sistema.

    Args:
        session: Sesión de base de datos.
        result: Resultado obtenido del conector.
        curation: Reglas de curación vigentes.
        now: Hora de finalización / observación (reloj inyectado).
        started_at: Hora en que comenzó la consulta.
        request_id: Petición del administrador que originó la consulta, si aplica.
        logo_fetcher: Descargador de imágenes inyectable.
        notify_fn: Función para emitir NOTIFY con los conjuntos de datos cambiados.
        follow_up: Ficha de equipo del "Resto" tras un listado: no es un listado, así que no
            cambia el estado de la consulta ni su base para RF-46; solo se anota en el registro.

    Returns:
        Informe de la ingesta (IngestReport).
    """
    instant = now or datetime.now(UTC)
    start = started_at or instant
    is_listing = result.job in LISTING_JOBS and not follow_up
    tracks_state = not follow_up

    # RF-46: Respuesta vacía donde antes había datos cuenta como consulta fallida (solo listados).
    state = session.get(SourceState, (result.source, result.job))
    baseline_state = state
    if baseline_state is None and is_listing:
        other_job = "initial_load" if result.job == "regular" else "regular"
        baseline_state = session.get(SourceState, (result.source, other_job))
    if is_listing and result.outcome in ("success", "partial"):
        is_totally_empty = (not result.records and not result.seen)
        is_empty_list = (result.item_count == 0)
        had_items = (baseline_state is not None and baseline_state.last_item_count is not None and baseline_state.last_item_count > 0)
        had_multiple = (baseline_state is not None and baseline_state.last_item_count is not None and baseline_state.last_item_count > 1)
        if (is_totally_empty and had_items) or (is_empty_list and had_multiple):
            result = replace(
                result,
                outcome="failure",
                message=f"Respuesta vacía donde antes había {baseline_state.last_item_count} elementos (RF-46)",
            )

    # Caso 1: Consulta prohibida por normas de la fuente (RF-42, RF-143)
    if result.outcome == "forbidden":
        if tracks_state:
            if state is None:
                state = SourceState(source=result.source, job=result.job)
                session.add(state)
            state.last_attempt_at = instant

        record_run(
            session,
            source=result.source,
            job=result.job,
            started_at=start,
            finished_at=instant,
            outcome="forbidden",
            message=result.message,
            request_id=request_id,
        )
        record_incident(
            session,
            kind="query_forbidden",
            source=result.source,
            subject=result.job,
            reason=result.message or "Consulta prohibida por las normas de la fuente",
            now=instant,
        )
        session.commit()
        return IngestReport()

    # Caso 2: Consulta fallida (RF-43 a RF-46, RF-141)
    if result.outcome == "failure":
        if tracks_state:
            if state is None:
                state = SourceState(source=result.source, job=result.job)
                session.add(state)
            state.last_attempt_at = instant

        record_run(
            session,
            source=result.source,
            job=result.job,
            started_at=start,
            finished_at=instant,
            outcome="failure",
            message=result.message,
            request_id=request_id,
        )
        record_incident(
            session,
            kind="query_failed",
            source=result.source,
            subject=result.job,
            reason=result.message or "Consulta fallida",
            now=instant,
        )
        session.commit()
        return IngestReport()

    # Caso 3: Consulta exitosa o parcial (RF-22, RF-47)
    report = ingest_records(session, result.records, curation=curation, now=instant, logo_fetcher=logo_fetcher)

    # Registrar rechazos del conector y de la ingesta (RF-142)
    for rej in result.rejected:
        record_incident(
            session,
            kind="data_rejected",
            source=result.source,
            subject=f"{rej.ref}:{rej.field}",
            reason=rej.reason,
            value=rej.value_excerpt,
            now=instant,
        )
    for rej in report.rejected:
        record_incident(
            session,
            kind="data_rejected",
            source=result.source,
            subject=f"record:{rej.index}",
            reason=rej.reason,
            now=instant,
        )
    for untranslated in report.untranslated_countries:
        record_incident(
            session,
            kind="data_rejected",
            source=result.source,
            subject=untranslated.ref,
            reason=untranslated.reason,
            now=instant,
        )

    # Discrepancias de cancelación (RF-53, RF-146): el partido y el motivo que da la ingesta.
    for discrepancy in report.discrepancies:
        record_incident(
            session,
            kind="cancel_discrepancy",
            source=result.source,
            subject=discrepancy.ref,
            reason=discrepancy.reason,
            now=instant,
        )

    # Registros retenidos (RF-55, RF-145)
    for ret in report.retained:
        record_incident(
            session,
            kind="record_retained",
            source=result.source,
            subject=str(ret),
            reason="Registro retenido sin enlazar a la fuente principal",
            now=instant,
        )

    # Avistamientos y detección de desapariciones (RF-50 a RF-52, RF-144)
    if result.seen:
        apply_sightings(session, result.seen, observed_at=instant)

    # RF-50: solo cuentan las consultas con éxito que listan todos los partidos de la fuente.
    listing_states = session.scalars(select(SourceState).where(
        SourceState.job.in_(LISTING_JOBS), SourceState.last_success_at.is_not(None))).all()
    last_success: dict = {}
    for listing_state in listing_states:
        last_success[listing_state.source] = max(last_success.get(listing_state.source, listing_state.last_success_at),
                                                 listing_state.last_success_at)
    if is_listing:
        last_success[result.source] = instant
    newly_disappeared = detect_disappearances(session, last_success, now=instant)
    for match_id in newly_disappeared:
        record_incident(
            session,
            kind="match_disappeared",
            source=result.source,
            subject=f"match:{match_id}",
            reason="Partido desaparecido tras 24 h sin aparecer en consultas con éxito",
            now=instant,
        )

    # Actualizar estado de la fuente (las fichas de equipo no lo cambian)
    if tracks_state:
        if state is None:
            state = SourceState(source=result.source, job=result.job)
            session.add(state)
        state.last_attempt_at = instant
        state.last_success_at = instant
        if result.item_count is not None:
            state.last_item_count = result.item_count

    # Completar tareas de carga inicial pendientes (RF-3, RF-13)
    if result.job == "initial_load" and result.outcome in ("success", "partial"):
        from app.db.models import SyncJob

        pending_jobs = session.scalars(
            select(SyncJob).where(SyncJob.kind == "initial_load", SyncJob.done_at.is_(None))
        ).all()
        for job in pending_jobs:
            job.done_at = instant

    # Resultado final de la ejecución: parcial si hubo rechazos (RF-105)
    final_outcome = result.outcome
    if result.rejected or report.rejected or report.untranslated_countries:
        final_outcome = "partial"

    record_run(
        session,
        source=result.source,
        job=result.job,
        started_at=start,
        finished_at=instant,
        outcome=final_outcome,
        message=result.message,
        request_id=request_id,
    )

    # Registrar marcas de cambio de conjuntos de datos y avisar por NOTIFY (RF-80, RF-81, RF-158)
    for ds in report.changed_datasets:
        dc = session.get(DatasetChange, ds)
        if dc is None:
            dc = DatasetChange(dataset=ds)
            session.add(dc)
        dc.last_changed_at = instant

    if report.changed_datasets:
        notify_changes(session, report.changed_datasets, now=instant)
        if notify_fn is not None:
            notify_fn(report.changed_datasets)

    session.commit()
    return report


def run_query(
    session: Session,
    query: PlannedQuery,
    client: PoliteClient,
    curation: Curation,
    now: datetime | None = None,
    logo_fetcher: Callable | None = None,
    notify_fn: Callable[[set[str]], None] | None = None,
    request_id: uuid.UUID | None = None,
) -> IngestReport:
    """Invoca al conector según la consulta planificada y ejecuta todo el pipeline.

    Args:
        session: Sesión de SQLAlchemy.
        query: Consulta planificada.
        client: Cliente HTTP educado de la fuente.
        curation: Reglas de curación.
        now: Hora actual (reloj inyectado).
        logo_fetcher: Descargador opcional de logos.
        notify_fn: Notificador opcional de cambios.
        request_id: Identificador de sync_request si viene de administración.

    Returns:
        IngestReport tras ejecutar la consulta.
    """
    instant = now or datetime.now(UTC)
    started_at = instant
    result = consult(query, client, instant)
    follow_up = query.team_id is not None

    return execute_consultation(
        session,
        result=result,
        curation=curation,
        now=instant,
        started_at=started_at,
        request_id=request_id,
        logo_fetcher=logo_fetcher,
        notify_fn=notify_fn,
        follow_up=follow_up,
    )
