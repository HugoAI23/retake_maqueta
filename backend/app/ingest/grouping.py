"""Agrupación de referencias en entidades y unión de filas (plan D-4).

Jugadores, franquicias, eventos, partidos y rosters se agrupan por los enlaces que
declaran las fuentes y, en el caso de los jugadores, por la curación. Los demás tipos
se identifican por su clave natural al resolverse (año, partido y posición…).
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import delete, select, tuple_, update
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    ExternalRef,
    Identity,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    Placement,
    PlacementRoster,
    PlayerGamertag,
    PlayerMapStats,
    RefLink,
    RosterMembership,
    Standing,
)
from app.domain.entity_links import group_refs
from app.ingest.store import KIND_MODELS

# Tipos que se agrupan por enlaces.
LINKED_KINDS = frozenset({"franchise", "player", "event", "match", "roster"})

# Filas que apuntan a cada tipo de entidad: (modelo, columna, columnas que forman con ella
# una clave única). Se usan para mover los datos al unir dos entidades.
REFERENCING = {
    "player": [
        (PlayerGamertag, "player_id", ("position",)),
        (RosterMembership, "player_id", ()),
        (PlayerMapStats, "player_id", ("map_id",)),
        (PlacementRoster, "player_id", ("placement_id",)),
    ],
    "franchise": [
        (Identity, "franchise_id", ("valid_from",)),
        (RosterMembership, "franchise_id", ()),
        (MatchSlot, "franchise_id", ()),
        (PlayerMapStats, "franchise_id", ()),
        (Standing, "franchise_id", ("season_id",)),
        (Placement, "franchise_id", ("championship_id",)),
    ],
    "event": [(Match, "event_id", ())],
    "match": [
        (MatchSchedule, "match_id", ("seq",)),
        (MatchSlot, "match_id", ("side",)),
        (MatchSlot, "origin_match_id", ()),
        (MatchMap, "match_id", ("position",)),
    ],
    "roster": [],
}


@dataclass
class RegroupResult:
    """Cambios de agrupación: entidades unidas (conservada, absorbida) y entidades nuevas por separación."""

    merged: list[tuple[uuid.UUID, uuid.UUID]] = field(default_factory=list)
    new_ids: set[uuid.UUID] = field(default_factory=set)
    split_from: set[uuid.UUID] = field(default_factory=set)

    @property
    def split(self) -> bool:
        return bool(self.split_from)

    @property
    def affected(self) -> set[uuid.UUID]:
        """Entidades que hay que recalcular: las que absorbieron a otra, las nuevas y las que perdieron referencias."""
        return {keep for keep, _ in self.merged} | self.new_ids | self.split_from


def regroup(session: Session, kind: str, merges=(), splits=()) -> RegroupResult:
    """Recalcula los grupos de referencias de un tipo y asigna `entity_id`.

    Cada grupo conserva el identificador de su referencia más antigua que ya tenga uno,
    salvo que otro grupo lo haya reclamado antes (separación): entonces recibe uno nuevo.

    Raises:
        CurationConflictError: si la curación une y separa las mismas referencias.
    """
    refs = list(session.scalars(select(ExternalRef).where(ExternalRef.kind == kind).order_by(ExternalRef.id)))
    by_key = {(ref.source, ref.source_id): ref for ref in refs}
    source_ref, target_ref = aliased(ExternalRef), aliased(ExternalRef)
    links = session.execute(
        select(source_ref.source, source_ref.source_id, target_ref.source, target_ref.source_id)
        .select_from(RefLink)
        .join(source_ref, source_ref.id == RefLink.from_ref_id)
        .join(target_ref, target_ref.id == RefLink.to_ref_id)
        .where(source_ref.kind == kind)
    ).all()
    groups = group_refs(
        by_key.keys(),
        source_links=[((a, b), (c, d)) for a, b, c, d in links],
        merges=[[(k.source, k.source_id) for k in merge] for merge in merges],
        splits=[tuple((k.source, k.source_id) for k in pair) for pair in splits],
    )

    result = RegroupResult()
    previous = {ref.id: ref.entity_id for ref in refs}
    claimed: set[uuid.UUID] = set()
    ordered = sorted(
        (sorted((by_key[k] for k in group if k in by_key), key=lambda r: r.id) for group in groups),
        key=lambda members: members[0].id if members else 0,
    )
    for members in ordered:
        if not members:
            continue
        existing = [m.entity_id for m in members if m.entity_id is not None]
        keep = next((entity for entity in existing if entity not in claimed), None)
        if keep is None:
            keep = uuid.uuid4()
            result.new_ids.add(keep)
            result.split_from.update(existing)
        claimed.add(keep)
        for member in members:
            member.entity_id = keep

    # Entidades que se han quedado sin referencias: sus referencias pasaron a otro grupo (unión).
    current = {ref.entity_id for ref in refs}
    for ref in refs:
        old = previous[ref.id]
        if old is not None and old not in current:
            pair = (ref.entity_id, old)
            if pair not in result.merged:
                result.merged.append(pair)
            current.add(old)  # la fila absorbida se une una sola vez
    session.flush()
    return result


def merge_entities(session: Session, kind: str, keep: uuid.UUID, drop: uuid.UUID) -> None:
    """Mueve a `keep` las filas que apuntaban a `drop` y borra la fila de `drop`.

    Si una fila movida chocaría con una clave única de `keep` (p. ej. dos posiciones de
    la misma temporada), se conserva la de `keep`.
    """
    model = KIND_MODELS[kind]
    if session.get(model, drop) is None:
        return
    if session.get(model, keep) is None:
        # La entidad conservada todavía no tiene fila: se reutiliza la de `drop`.
        session.execute(update(ExternalRef).where(ExternalRef.kind == kind, ExternalRef.entity_id == keep)
                        .values(entity_id=drop))
        return
    for child, column, unique_with in REFERENCING.get(kind, []):
        fk = getattr(child, column)
        if unique_with:
            cols = [getattr(child, name) for name in unique_with]
            clash = select(*cols).where(fk == keep)
            session.execute(delete(child).where(fk == drop, tuple_(*cols).in_(clash)))
        session.execute(update(child).where(fk == drop).values({column: keep}))
    session.execute(delete(model).where(model.id == drop))
    session.flush()
