"""Partido prioritario con varios partidos en vivo (spec 003: RF-23 a RF-26).

Cada ciclo en vivo consulta la lista de partidos en vivo y la página de cada partido. Si la
pausa mínima entre consultas no deja hacerlo todo en 60 s, el partido prioritario se sigue
consultando cada 60 s y los demás cada 2 minutos.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.vocabulary import LIVE_CYCLE, SECONDARY_LIVE_CYCLE


@dataclass(frozen=True)
class LiveMatch:
    """Partido en vivo con su hora de inicio programada."""

    id: str
    scheduled_at: datetime


def prioritary_match(matches: Sequence[LiveMatch], spotlight_id: str | None = None) -> str | None:
    """El que destaca la spec del spotlight (RF-25); sin ella, el que empezó antes (RF-26).

    Empates de hora de inicio: se desempata por identificador para que sea estable.
    """
    if not matches:
        return None
    if spotlight_id is not None and any(m.id == spotlight_id for m in matches):
        return spotlight_id
    return min(matches, key=lambda m: (m.scheduled_at, m.id)).id


def live_cycles(
    matches: Sequence[LiveMatch], pause: timedelta, spotlight_id: str | None = None
) -> dict[str, timedelta]:
    """Ciclo de consulta de cada partido en vivo.

    Args:
        matches: Partidos en vivo.
        pause: Pausa mínima entre consultas a la fuente (RF-39).
        spotlight_id: Partido destacado por la spec del spotlight, si existe.

    Returns:
        60 s para todos si caben (una consulta de la lista más una por partido); si no,
        60 s para el prioritario y 2 minutos para los demás.
    """
    if not matches:
        return {}
    needed = pause * (1 + len(matches))
    if needed <= LIVE_CYCLE:
        return {m.id: LIVE_CYCLE for m in matches}
    first = prioritary_match(matches, spotlight_id)
    return {m.id: LIVE_CYCLE if m.id == first else SECONDARY_LIVE_CYCLE for m in matches}
