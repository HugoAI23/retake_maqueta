"""Referencias externas, enlaces y observaciones (plan de la spec 002, §3.1 y D-2)."""

import uuid
from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import datetime

from pydantic_core import to_jsonable_python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Championship,
    Event,
    ExternalRef,
    Franchise,
    Identity,
    Match,
    MatchMap,
    Observation,
    Placement,
    Player,
    PlayerMapStats,
    RefLink,
    RosterMembership,
    Season,
    Standing,
)
from app.domain.priority import SOURCE_PRIORITY, SourceValue, choose
from app.ingest.records import RefKey

# Tabla resuelta de cada tipo de registro: `external_ref.entity_id` apunta a una fila de ella.
KIND_MODELS = {
    "season": Season,
    "event": Event,
    "franchise": Franchise,
    "identity": Identity,
    "player": Player,
    "roster": RosterMembership,
    "match": Match,
    "match_map": MatchMap,
    "player_map_stats": PlayerMapStats,
    "standing": Standing,
    "championship": Championship,
    "placement": Placement,
}


class UnknownReferenceError(LookupError):
    """Un registro apunta a un objeto que todavía no existe en Retake."""

    def __init__(self, kind: str, key: RefKey):
        super().__init__(f"Referencia desconocida: {kind} {key}")


def as_key(value: RefKey | str | dict) -> RefKey:
    return value if isinstance(value, RefKey) else RefKey.model_validate(value)


def find_ref(session: Session, kind: str, key: RefKey | str) -> ExternalRef | None:
    key = as_key(key)
    return session.scalar(
        select(ExternalRef).where(
            ExternalRef.kind == kind, ExternalRef.source == key.source, ExternalRef.source_id == key.source_id
        )
    )


def ensure_ref(session: Session, kind: str, key: RefKey, fictional: bool = False) -> ExternalRef:
    """Devuelve la referencia externa, creándola si no existe."""
    ref = find_ref(session, kind, key)
    if ref is None:
        ref = ExternalRef(kind=kind, source=key.source, source_id=key.source_id, fictional=fictional)
        session.add(ref)
        session.flush()
    elif fictional and not ref.fictional:
        ref.fictional = True
    return ref


def entity_for(session: Session, kind: str, key: RefKey | str) -> uuid.UUID | None:
    """Entidad interna de una referencia externa (p. ej. `entity_for(s, "player", "bp:12")`)."""
    ref = find_ref(session, kind, key)
    return None if ref is None else ref.entity_id


def require_entity(session: Session, kind: str, key: RefKey | str | dict) -> uuid.UUID:
    """Como `entity_for`, pero falla si la referencia no existe o no tiene entidad."""
    key = as_key(key)
    entity_id = entity_for(session, kind, key)
    if entity_id is None or session.get(KIND_MODELS[kind], entity_id) is None:
        raise UnknownReferenceError(kind, key)
    return entity_id


def refs_of_entity(session: Session, kind: str, entity_id: uuid.UUID) -> list[ExternalRef]:
    return list(
        session.scalars(
            select(ExternalRef)
            .where(ExternalRef.kind == kind, ExternalRef.entity_id == entity_id)
            .order_by(ExternalRef.id)
        )
    )


def add_link(session: Session, from_ref: ExternalRef, to_ref: ExternalRef, link_type: str) -> None:
    exists = session.scalar(
        select(RefLink.id).where(
            RefLink.from_ref_id == from_ref.id, RefLink.to_ref_id == to_ref.id, RefLink.link_type == link_type
        )
    )
    if exists is None and from_ref.id != to_ref.id:
        session.add(RefLink(from_ref_id=from_ref.id, to_ref_id=to_ref.id, link_type=link_type))
        session.flush()


def upsert_observation(
    session: Session,
    ref: ExternalRef,
    field: str,
    value: object,
    is_valid: bool,
    observed_at: datetime,
    created: set[tuple[int, str]],
) -> None:
    """Guarda el último valor que publica una fuente para un campo.

    Una observación más antigua que la guardada se ignora, para que un dato atrasado
    no pise uno más reciente.
    """
    json_value = to_jsonable_python(value)
    obs = session.scalar(select(Observation).where(Observation.ref_id == ref.id, Observation.field == field))
    if obs is None:
        session.add(
            Observation(
                ref_id=ref.id, field=field, value=json_value, is_valid=is_valid,
                first_seen_at=observed_at, last_seen_at=observed_at,
            )
        )
        created.add((ref.id, field))
    elif observed_at >= obs.last_seen_at:
        obs.value, obs.is_valid, obs.last_seen_at = json_value, is_valid, observed_at


class ObservationIndex:
    """Observaciones de un grupo de referencias (una entidad), agrupadas por campo."""

    def __init__(self, session: Session, refs: Sequence[ExternalRef]):
        self._by_field: dict[str, list[tuple[int, SourceValue]]] = defaultdict(list)
        ids = [ref.id for ref in refs]
        if not ids:
            return
        rows = session.execute(
            select(Observation, ExternalRef.source)
            .join(ExternalRef, ExternalRef.id == Observation.ref_id)
            .where(Observation.ref_id.in_(ids))
        ).all()
        for obs, source in rows:
            self._by_field[obs.field].append(
                (obs.ref_id, SourceValue(source, obs.value, obs.is_valid, obs.last_seen_at))
            )

    def pick(self, field: str, order: Sequence[str] = SOURCE_PRIORITY) -> SourceValue | None:
        return choose((value for _, value in self._by_field.get(field, [])), order)

    def value(self, field: str, order: Sequence[str] = SOURCE_PRIORITY) -> object:
        winner = self.pick(field, order)
        return None if winner is None else winner.value

    def has(self, field: str) -> bool:
        return field in self._by_field

    def had_previous(self, field: str, created: set[tuple[int, str]]) -> bool:
        """El campo ya había recibido alguna observación antes del registro actual (RF-98)."""
        return any((ref_id, field) not in created for ref_id, _ in self._by_field.get(field, []))

    def latest_seen(self) -> datetime | None:
        seen = [value.last_seen_at for values in self._by_field.values() for _, value in values]
        return max(seen, default=None)


def delete_refs(session: Session, refs: Iterable[ExternalRef]) -> None:
    for ref in refs:
        session.delete(ref)
    session.flush()
