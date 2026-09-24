"""Entrada de registros de fuente (plan de la spec 002, §1.2).

Por cada registro:
1. se comprueba su forma (`records`);
2. se guardan sus referencias, enlaces y observaciones, también las no válidas;
3. se reagrupan las referencias si el tipo se agrupa por enlaces;
4. se recalcula la entidad a partir de sus observaciones (`resolvers`).

Cada registro se aplica en su propio punto de guardado: si falla, se deshace solo ese
registro y el motivo queda en el informe. Quien llama confirma la transacción.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.curation.loader import Curation, load_curation
from app.db.models import ExternalRef, Player, RefLink
from app.domain.entity_links import CurationConflictError
from app.ingest.changes import ChangeTracker
from app.ingest.completeness import update_stats_complete
from app.ingest.retention import update_retention
from app.ingest.weeks import update_weeks
from app.ingest.fields import FIELD_EXTRACTORS
from app.ingest.grouping import LINKED_KINDS, merge_entities, regroup
from app.ingest.records import RecordError, parse_record
from app.ingest.resolvers import (
    RESOLVERS,
    IngestContext,
    PERSONAL_FIELDS,
    IngestError,
    collapse_repeated_identities,
    delete_orphan_rows,
    removal_requested,
    reresolve_all_refs,
    reresolve_entity,
)
from app.ingest.rollover import roll_over
from app.ingest.store import UnknownReferenceError, add_link, ensure_ref, upsert_observation


# Campo del registro → observaciones en que se guarda, cuando no coinciden (spec 003, T-037).
UNREADABLE_FIELDS = {
    "maps_won": ("maps_won_1", "maps_won_2"),
    "slots": ("slot_1", "slot_2"),
    "live_map": ("live_mode", "live_score_1", "live_score_2"),
    "score": ("score_1", "score_2"),
    "from_": ("from",),
}


@dataclass
class Rejection:
    """Registro rechazado: su posición en la entrada y el motivo."""

    index: int
    reason: str


@dataclass
class IngestReport:
    """Resultado de una ingesta.

    `changed_datasets` son los conjuntos de datos que cambiaron (spec 003, RF-158): el proceso
    de obtención avisa con ellos a la API. `discarded` cuenta los rosters de equipos que no son de
    la CDL ni invitados, que se descartan sin anotarlos (RF-18c de la 003; cambio C-26).
    """

    accepted: int = 0
    rejected: list[Rejection] = field(default_factory=list)
    discarded: int = 0
    changed_datasets: set[str] = field(default_factory=set)
    discrepancies: list = field(default_factory=list)
    retained: list[str] = field(default_factory=list)
    untranslated_countries: list = field(default_factory=list)


# Spec 003 (T-044): tipos que se recalculan tras unir entidades de la curación.
MERGE_DEPENDENTS = {
    "franchise": ("identity", "roster", "standing", "placement", "match"),
    "event": ("match",),
    "match": ("match_map",),
}


def apply_regroup(ctx: IngestContext, kind: str, skip: set | None = None) -> None:
    """Reagrupa las referencias de un tipo y recalcula las entidades afectadas.

    Raises:
        CurationConflictError: si la curación une y separa las mismas referencias.
    """
    if kind == "player":
        merges = [entry.players for entry in ctx.curation.player_merges]
    else:  # spec 003 (RF-54): uniones de partidos, eventos y franquicias
        merges = [entry.refs for entry in ctx.curation.merges if entry.kind == kind]
    splits = ctx.curation.player_splits if kind == "player" else []
    result = regroup(ctx.session, kind, merges=merges, splits=[entry.players for entry in splits])
    for keep, drop in result.merged:
        merge_entities(ctx.session, kind, keep, drop)
    for entity_id in result.affected - (skip or set()):
        reresolve_entity(ctx, kind, entity_id)
    if kind == "player" and result.split:
        # Al separar jugadores, sus rosters, estadísticas e historial pueden cambiar de dueño.
        for dependent in ("roster", "player_map_stats", "placement"):
            reresolve_all_refs(ctx, dependent)
    if result.merged and kind in MERGE_DEPENDENTS:
        # Spec 003: al unir, lo que colgaba de cada parte se recalcula junto (p. ej. la identidad combinada).
        for dependent in MERGE_DEPENDENTS[kind]:
            reresolve_all_refs(ctx, dependent)
    if kind == "franchise":
        # Plan I-37: cada parte traía su identidad; tras recalcularlas no deben quedar dos iguales seguidas.
        for keep, _ in result.merged:
            collapse_repeated_identities(ctx, keep)


def confirmed_keys(curation: Curation) -> set[tuple[str, str, str]]:
    """Referencias que la curación confirma como nuevas: no se retienen (spec 003, RF-56)."""
    return {(entry.kind, entry.ref.source, entry.ref.source_id) for entry in curation.confirmed_new}


def _personal_data_removed(ctx: IngestContext, ref: ExternalRef) -> bool:
    """La referencia es de un jugador retirado, o de uno enlazado a él, o la curación lo pide."""
    session = ctx.session
    linked = select(RefLink).where(RefLink.link_type == "same_as",
                                   or_(RefLink.from_ref_id == ref.id, RefLink.to_ref_id == ref.id))
    other_ids = {link.to_ref_id if link.from_ref_id == ref.id else link.from_ref_id for link in session.scalars(linked)}
    related = [ref, *session.scalars(select(ExternalRef).where(ExternalRef.id.in_(other_ids)))]
    if removal_requested(ctx, related):
        return True
    entities = {r.entity_id for r in related if r.entity_id is not None}
    return bool(entities) and session.scalar(
        select(func.count()).select_from(Player)
        .where(Player.id.in_(entities), Player.personal_data_removed.is_(True))) > 0


def ingest_one(ctx: IngestContext, record) -> None:
    session = ctx.session
    ref = ensure_ref(session, record.kind, record.key, record.fictional)
    for other in record.same_as:
        add_link(session, ref, ensure_ref(session, record.kind, other, record.fictional), "same_as")
    if record.kind == "franchise" and record.predecessor is not None:
        add_link(session, ref, ensure_ref(session, "franchise", record.predecessor), "predecessor")
    # Spec 003 (RF-60): los datos personales de un jugador retirado no se guardan, ni un instante.
    skipped = PERSONAL_FIELDS if record.kind == "player" and _personal_data_removed(ctx, ref) else ()
    for name, value, is_valid in FIELD_EXTRACTORS[record.kind](record, session):
        if name in skipped:
            continue
        upsert_observation(session, ref, name, value, is_valid, record.observed_at, ctx.created)
    for name in record.unreadable:  # spec 003: datos publicados pero no entendidos (RF-48, RF-49)
        for field_name in UNREADABLE_FIELDS.get(name, (name,)):
            if field_name in skipped:
                continue
            upsert_observation(session, ref, field_name, None, False, record.observed_at, ctx.created,
                               invalid_reason="unreadable")
    session.flush()

    if record.kind in LINKED_KINDS:
        own_entity = ref.entity_id
        apply_regroup(ctx, record.kind, skip={own_entity} if own_entity else None)
        session.refresh(ref)
    RESOLVERS[record.kind](ctx, ref)


def ingest_records(
    session: Session,
    raw_records: Iterable[object],
    curation: Curation | None = None,
    now: datetime | None = None,
    logo_fetcher: Callable[[str], bytes] | None = None,
) -> IngestReport:
    """Aplica una secuencia de registros de fuente en el orden dado.

    Args:
        curation: Curación vigente. Si no se indica, se lee el archivo del proyecto,
            para que una ingesta nunca deshaga una unión o separación de la curación.
        now: Hora de la ingesta, que queda como `changed_at` de lo que cambie (spec 003,
            RF-157). Las pruebas la fijan; por defecto, la hora actual en UTC.
        logo_fetcher: Descarga la imagen de un logo (spec 003, RF-65 a RF-71); lanza
            `InvalidLogo` si no se puede. Sin él, los logos no se descargan.
    """
    ctx = IngestContext(session=session, curation=curation if curation is not None else load_curation())
    report = IngestReport()
    tracker = ChangeTracker(now or datetime.now(UTC))
    ctx.now, ctx.logo_fetcher = tracker.now, logo_fetcher
    tracker.attach(session)
    try:
        _ingest_all(ctx, raw_records, report, tracker)
        update_stats_complete(session, tracker.now)
        update_weeks(session)
        report.retained = update_retention(session, tracker.now, confirmed_keys(ctx.curation))
        tracker.save(session)
    finally:
        tracker.detach()
    report.changed_datasets = set(tracker.changed)
    report.discrepancies = list(dict.fromkeys(ctx.discrepancies))
    report.untranslated_countries = list(dict.fromkeys(ctx.untranslated_countries))
    return report


def _ingest_all(ctx: IngestContext, raw_records: Iterable[object], report: IngestReport, tracker: ChangeTracker) -> None:
    session = ctx.session
    for index, raw in enumerate(raw_records):
        try:
            record = parse_record(raw)
        except RecordError as error:
            report.rejected.append(Rejection(index, str(error)))
            continue

        ctx.created = set()
        savepoint = session.begin_nested()
        try:
            ingest_one(ctx, record)
            savepoint.commit()
            report.accepted += 1
        except UnknownReferenceError as error:
            savepoint.rollback()
            ctx.pending_rollover = None
            if record.kind == "roster" and error.kind == "franchise":
                # Etapa del jugador en un equipo que no es de la CDL ni invitado (RF-18c; C-26).
                report.discarded += 1
            else:
                report.rejected.append(Rejection(index, str(error)))
            continue
        except (IngestError, CurationConflictError) as error:
            savepoint.rollback()
            ctx.pending_rollover = None
            report.rejected.append(Rejection(index, str(error)))
            continue

        if ctx.pending_rollover is not None:
            roll_over(session, ctx.pending_rollover)
            tracker.rolled_over()
            ctx.pending_rollover = None

    delete_orphan_rows(session)
