"""Referencias vistas y partidos desaparecidos (spec 003: RF-50 a RF-52; plan §2.3).

- Cada consulta con éxito anota qué partidos incluía (`external_ref.last_seen_at`).
- Un partido desaparece cuando lleva 24 h sin aparecer en ninguna consulta con éxito de las
  fuentes que lo publicaban (`domain.disappearance`). Se conserva tal como estaba, también en
  vivo: solo se anota `disappeared_at`, que la API y la incidencia usan (RF-51, RF-144).
- Si vuelve a aparecer, se quita la marca y se sigue actualizando con normalidad (RF-52).
"""

import uuid
from collections.abc import Iterable, Mapping
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ExternalRef, Match
from app.domain.disappearance import Sighting, is_disappeared
from app.ingest.store import as_key


def apply_sightings(session: Session, seen: Iterable[str], observed_at: datetime) -> list[uuid.UUID]:
    """Anota que la consulta con éxito de `observed_at` incluía estos partidos.

    Returns:
        Los partidos que estaban desaparecidos y han reaparecido.
    """
    reappeared = []
    for raw in seen:
        key = as_key(raw)
        ref = session.scalar(select(ExternalRef).where(
            ExternalRef.kind == "match", ExternalRef.source == key.source, ExternalRef.source_id == key.source_id))
        if ref is None:
            continue
        if ref.last_seen_at is None or observed_at > ref.last_seen_at:
            ref.last_seen_at = observed_at
        match = session.get(Match, ref.entity_id) if ref.entity_id else None
        if match is not None and match.disappeared_at is not None:
            match.disappeared_at = None
            reappeared.append(match.id)
    session.flush()
    return reappeared


def detect_disappearances(session: Session, last_success: Mapping[str, datetime], now: datetime) -> list[uuid.UUID]:
    """Marca como desaparecidos los partidos que cumplen RF-50 y devuelve los recién marcados.

    Args:
        last_success: Última consulta con éxito de cada fuente que lista partidos.
        now: Hora actual (reloj inyectado).
    """
    refs = session.scalars(select(ExternalRef).where(
        ExternalRef.kind == "match", ExternalRef.entity_id.is_not(None), ExternalRef.last_seen_at.is_not(None))).all()
    by_match: dict[uuid.UUID, list[Sighting]] = {}
    for ref in refs:
        if ref.source in last_success:
            by_match.setdefault(ref.entity_id, []).append(Sighting(ref.source, ref.last_seen_at, last_success[ref.source]))
    newly = []
    for match_id, sightings in by_match.items():
        match = session.get(Match, match_id)
        if match is not None and match.disappeared_at is None and is_disappeared(sightings):
            match.disappeared_at = now
            newly.append(match_id)
    session.flush()
    return newly
