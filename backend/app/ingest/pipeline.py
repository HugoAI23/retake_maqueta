"""Entrada de registros de fuente (plan de la spec 002, §1.2).

Por cada registro:
1. se comprueba su forma (`records`);
2. se guardan sus referencias, enlaces y observaciones, también las no válidas;
3. se reagrupan las referencias si el tipo se agrupa por enlaces;
4. se recalcula la entidad a partir de sus observaciones (`resolvers`).

Cada registro se aplica en su propio punto de guardado: si falla, se deshace solo ese
registro y el motivo queda en el informe. Quien llama confirma la transacción.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.curation.loader import Curation, load_curation
from app.domain.entity_links import CurationConflictError
from app.ingest.fields import FIELD_EXTRACTORS
from app.ingest.grouping import LINKED_KINDS, merge_entities, regroup
from app.ingest.records import RecordError, parse_record
from app.ingest.resolvers import (
    RESOLVERS,
    IngestContext,
    IngestError,
    delete_orphan_rows,
    reresolve_all_refs,
    reresolve_entity,
)
from app.ingest.rollover import roll_over
from app.ingest.store import UnknownReferenceError, add_link, ensure_ref, upsert_observation


@dataclass
class Rejection:
    """Registro rechazado: su posición en la entrada y el motivo."""

    index: int
    reason: str


@dataclass
class IngestReport:
    accepted: int = 0
    rejected: list[Rejection] = field(default_factory=list)


def apply_regroup(ctx: IngestContext, kind: str, skip: set | None = None) -> None:
    """Reagrupa las referencias de un tipo y recalcula las entidades afectadas.

    Raises:
        CurationConflictError: si la curación une y separa las mismas referencias.
    """
    merges = ctx.curation.player_merges if kind == "player" else []
    splits = ctx.curation.player_splits if kind == "player" else []
    result = regroup(
        ctx.session, kind,
        merges=[entry.players for entry in merges],
        splits=[entry.players for entry in splits],
    )
    for keep, drop in result.merged:
        merge_entities(ctx.session, kind, keep, drop)
    for entity_id in result.affected - (skip or set()):
        reresolve_entity(ctx, kind, entity_id)
    if kind == "player" and result.split:
        # Al separar jugadores, sus rosters, estadísticas e historial pueden cambiar de dueño.
        for dependent in ("roster", "player_map_stats", "placement"):
            reresolve_all_refs(ctx, dependent)


def ingest_one(ctx: IngestContext, record) -> None:
    session = ctx.session
    ref = ensure_ref(session, record.kind, record.key, record.fictional)
    for other in record.same_as:
        add_link(session, ref, ensure_ref(session, record.kind, other, record.fictional), "same_as")
    if record.kind == "franchise" and record.predecessor is not None:
        add_link(session, ref, ensure_ref(session, "franchise", record.predecessor), "predecessor")
    for name, value, is_valid in FIELD_EXTRACTORS[record.kind](record, session):
        upsert_observation(session, ref, name, value, is_valid, record.observed_at, ctx.created)
    session.flush()

    if record.kind in LINKED_KINDS:
        own_entity = ref.entity_id
        apply_regroup(ctx, record.kind, skip={own_entity} if own_entity else None)
        session.refresh(ref)
    RESOLVERS[record.kind](ctx, ref)


def ingest_records(session: Session, raw_records: Iterable[object], curation: Curation | None = None) -> IngestReport:
    """Aplica una secuencia de registros de fuente en el orden dado.

    Args:
        curation: Curación vigente. Si no se indica, se lee el archivo del proyecto,
            para que una ingesta nunca deshaga una unión o separación de la curación.
    """
    ctx = IngestContext(session=session, curation=curation if curation is not None else load_curation())
    report = IngestReport()
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
        except (UnknownReferenceError, IngestError, CurationConflictError) as error:
            savepoint.rollback()
            ctx.pending_rollover = None
            report.rejected.append(Rejection(index, str(error)))
            continue

        if ctx.pending_rollover is not None:
            roll_over(session, ctx.pending_rollover)
            ctx.pending_rollover = None

    delete_orphan_rows(session)
    return report
