"""Partidos que dejan de aparecer en las fuentes (spec 003: RF-50 a RF-52, RF-90).

La ausencia solo cuenta si está comprobada por consultas **con éxito**: una fuente caída
no hace desaparecer nada. Un partido falta de una fuente desde la última vez que la vio,
y esa ausencia está comprobada hasta su última consulta con éxito.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.vocabulary import DISAPPEARED_AFTER, LIVE_MISSING_AFTER


@dataclass(frozen=True)
class Sighting:
    """Lo que se sabe de un partido en una de las fuentes que lo publicaban.

    Attributes:
        source: La fuente.
        last_seen_at: Última consulta con éxito que incluía el partido.
        last_success_at: Última consulta con éxito de esa fuente (lo incluyera o no).
    """

    source: str
    last_seen_at: datetime
    last_success_at: datetime


def _missing_for(sightings: Iterable[Sighting], threshold: timedelta) -> bool:
    sightings = list(sightings)
    if not sightings:
        return False
    return all(s.last_success_at - s.last_seen_at >= threshold for s in sightings)


def is_disappeared(sightings: Iterable[Sighting]) -> bool:
    """Desaparecido: 24 h de ausencia comprobada en todas las fuentes que lo publicaban (RF-50)."""
    return _missing_for(sightings, DISAPPEARED_AFTER)


def is_missing_live(sightings: Iterable[Sighting]) -> bool:
    """Partido en vivo que lleva 60 s sin aparecer: sus bloques muestran el aviso (RF-90)."""
    return _missing_for(sightings, LIVE_MISSING_AFTER)
