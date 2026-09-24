"""Registros retenidos y candidatos parecidos (spec 003: RF-54, RF-56; T-047).

Ayuda a Hugo a decidir qué unir o confirmar como nuevo en `curation.yaml`. Solo lee y sugiere:
nunca une nada (RF-132 de la 002).
"""

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Event, ExternalRef, Identity, Match, MatchSchedule, MatchSlot, Player
from app.domain.priority import SOURCE_PRIORITY
from app.domain.vocabulary import SUMMARY_TIMEZONE
from app.ingest.retention import RETAINABLE

MEXICO_CITY = ZoneInfo(SUMMARY_TIMEZONE)


@dataclass(frozen=True)
class Candidate:
    ref: str
    label: str


@dataclass
class RetainedItem:
    kind: str
    ref: str
    since: datetime
    label: str
    candidates: list[Candidate] = field(default_factory=list)


def _franchise_name(session: Session, franchise_id) -> str | None:
    identity = session.scalars(select(Identity).where(Identity.franchise_id == franchise_id)
                               .order_by(Identity.valid_from.desc())).first()
    return identity.short_name if identity else None


def _label(session: Session, kind: str, entity_id) -> str:
    if kind == "player":
        return session.get(Player, entity_id).current_gamertag
    if kind == "franchise":
        return _franchise_name(session, entity_id) or "(sin identidad)"
    if kind == "event":
        return session.get(Event, entity_id).name
    teams, day = _match_key(session, entity_id)
    return f"{' vs '.join(sorted(teams)) or '(equipos sin conocer)'} · {day or 'sin fecha'}"


def _match_key(session: Session, match_id) -> tuple[frozenset[str], str | None]:
    """Equipos (por nombre) y día del partido en hora de Ciudad de México."""
    franchises = session.scalars(select(MatchSlot.franchise_id).where(
        MatchSlot.match_id == match_id, MatchSlot.franchise_id.is_not(None))).all()
    teams = frozenset(name.casefold() for name in (_franchise_name(session, f) for f in franchises) if name)
    scheduled = session.scalars(select(MatchSchedule.scheduled_at).where(MatchSchedule.match_id == match_id)
                                .order_by(MatchSchedule.seq.desc())).first()
    return teams, scheduled.astimezone(MEXICO_CITY).date().isoformat() if scheduled else None


def _key(session: Session, kind: str, entity_id) -> object:
    """Clave de parecido: mismo gamertag, mismo nombre, o mismos equipos y fecha."""
    if kind == "match":
        teams, day = _match_key(session, entity_id)
        return (teams, day) if len(teams) == 2 and day else None
    label = _label(session, kind, entity_id)
    return label.casefold() if label else None


def list_retained(session: Session) -> list[RetainedItem]:
    """Registros retenidos, cada uno con los objetos visibles que se le parecen. No cambia nada."""
    items = []
    for kind in RETAINABLE:
        refs = session.scalars(select(ExternalRef).where(ExternalRef.kind == kind).order_by(ExternalRef.id)).all()
        visible: dict = {}
        for ref in refs:
            if ref.retained_since is None and ref.entity_id is not None:
                visible.setdefault(ref.entity_id, []).append(ref)
        keys = {entity_id: _key(session, kind, entity_id) for entity_id in visible}
        for ref in refs:
            if ref.retained_since is None or ref.entity_id is None:
                continue
            key = _key(session, kind, ref.entity_id)
            candidates = []
            for entity_id, entity_refs in visible.items():
                if key is not None and keys[entity_id] == key:
                    best = min(entity_refs, key=lambda r: SOURCE_PRIORITY.index(r.source) if r.source in SOURCE_PRIORITY else 99)
                    candidates.append(Candidate(f"{best.source}:{best.source_id}", _label(session, kind, entity_id)))
            items.append(RetainedItem(kind, f"{ref.source}:{ref.source_id}", ref.retained_since,
                                      _label(session, kind, ref.entity_id), candidates))
    return items
