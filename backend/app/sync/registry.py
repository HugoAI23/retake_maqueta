"""Registro de actualizaciones e incidencias (spec 003: RF-140 a RF-149; T-050).

Guarda el resultado de cada consulta a una fuente, agrupa las incidencias idénticas
sin repeticiones (actualizando contador y última hora), computa repeticiones diarias
por fecha de Ciudad de México y purga registros con más de 7 días.
"""

import hashlib
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import DailySummary, Incident, IncidentDay, SyncRun
from app.domain.vocabulary import (
    INCIDENT_KINDS,
    RETENTION,
    RUN_OUTCOMES,
    SOURCES,
    SUMMARY_TIMEZONE,
    SYNC_JOBS,
)
from app.sources.contract import plain_message


def record_run(
    session: Session,
    source: str,
    job: str,
    started_at: datetime,
    finished_at: datetime,
    outcome: str,
    message: object = None,
    request_id: uuid.UUID | None = None,
) -> SyncRun:
    """Registra una consulta en sync_run (RF-140, RF-141).

    Args:
        session: Sesión de SQLAlchemy.
        source: Fuente consultada ("bp", "wiki", "cdl").
        job: Tipo de consulta ("initial_load", "regular", "live", etc.).
        started_at: Inicio de la consulta.
        finished_at: Fin de la consulta.
        outcome: Resultado ("success", "partial", "failure", "forbidden").
        message: Mensaje o error, formateado como texto plano y recortado a 500 caracteres.
        request_id: Petición del administrador que originó la consulta, si aplica.

    Returns:
        Entrada creada en SyncRun.
    """
    if source not in SOURCES:
        raise ValueError(f"Fuente desconocida: {source!r}")
    if job not in SYNC_JOBS:
        raise ValueError(f"Tipo de consulta desconocido: {job!r}")
    if outcome not in RUN_OUTCOMES:
        raise ValueError(f"Resultado desconocido: {outcome!r}")

    run = SyncRun(
        source=source,
        job=job,
        started_at=started_at,
        finished_at=finished_at,
        outcome=outcome,
        message=plain_message(message),
        request_id=request_id,
    )
    session.add(run)
    session.flush()
    return run


def record_incident(
    session: Session,
    kind: str,
    subject: str,
    reason: str,
    source: str | None = None,
    value: object = None,
    detail: object = None,
    now: datetime | None = None,
) -> Incident:
    """Anota una incidencia en el registro sin duplicar incidencias idénticas (RF-142 a RF-148).

    - Una incidencia idéntica (misma fuente, tipo, dato/asunto, huella de valor y motivo)
      actualiza repetitions y last_at en vez de crear una fila nueva (RF-147, RF-148).
    - value_hash almacena únicamente el hash SHA-256 del valor rechazado, nunca el valor
      en claro, garantizando que no se guarden datos personales (plan §9, RF-60).
    - Actualiza además incident_day para la fecha en curso de Ciudad de México (RF-150 a RF-152).

    Returns:
        La fila de Incident (creada o actualizada).
    """
    if kind not in INCIDENT_KINDS:
        raise ValueError(f"Tipo de incidencia desconocido: {kind!r}")
    if source is not None and source not in SOURCES:
        raise ValueError(f"Fuente desconocida: {source!r}")

    instant = now or datetime.now(UTC)
    clean_reason = plain_message(reason) or "Sin motivo"
    clean_detail = plain_message(detail)
    clean_subject = str(subject)[:255]

    value_hash = (
        hashlib.sha256(str(value).encode("utf-8")).hexdigest()
        if value is not None
        else None
    )

    stmt = select(Incident).where(
        Incident.source.is_not_distinct_from(source),
        Incident.kind == kind,
        Incident.subject == clean_subject,
        Incident.value_hash.is_not_distinct_from(value_hash),
        Incident.reason == clean_reason,
    )
    incident = session.scalar(stmt)

    if incident is not None:
        incident.repetitions += 1
        incident.last_at = instant
        if clean_detail and not incident.detail:
            incident.detail = clean_detail
    else:
        incident = Incident(
            source=source,
            kind=kind,
            subject=clean_subject,
            value_hash=value_hash,
            reason=clean_reason,
            detail=clean_detail,
            first_at=instant,
            last_at=instant,
            repetitions=1,
        )
        session.add(incident)
        session.flush()

    # Repeticiones del día natural en Ciudad de México (RF-150)
    day_cdmx = instant.astimezone(ZoneInfo(SUMMARY_TIMEZONE)).date()
    day_entry = session.get(IncidentDay, (incident.id, day_cdmx))
    if day_entry is not None:
        day_entry.repetitions += 1
    else:
        session.add(IncidentDay(incident_id=incident.id, day=day_cdmx, repetitions=1))

    session.flush()
    return incident


def purge_old_entries(session: Session, now: datetime) -> int:
    """Elimina del registro las entradas con más de 7 días (RF-149, RF-154).

    Args:
        session: Sesión de SQLAlchemy.
        now: Hora actual (reloj inyectado).

    Returns:
        Número total de registros eliminados (SyncRun + Incident + DailySummary).
    """
    cutoff = now - RETENTION
    cutoff_day = (now.astimezone(ZoneInfo(SUMMARY_TIMEZONE)) - RETENTION).date()

    res_runs = session.execute(delete(SyncRun).where(SyncRun.finished_at < cutoff))
    res_inc = session.execute(delete(Incident).where(Incident.last_at < cutoff))
    res_sum = session.execute(delete(DailySummary).where(DailySummary.day < cutoff_day))

    session.flush()
    return res_runs.rowcount + res_inc.rowcount + res_sum.rowcount
