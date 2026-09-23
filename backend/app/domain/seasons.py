"""Temporada actual (RF-2, RF-3, RF-52, RF-53, RF-123; plan §3.5 y D-7).

La temporada actual no se guarda: se calcula a partir del instante en que empezó
cada temporada. Una temporada empieza cuando cualquier partido oficial suyo, incluidos
los Qualifiers, pasa a en vivo (RF-3, RF-53), y ese inicio no se borra nunca (RF-123).
"""

from collections.abc import Mapping
from datetime import datetime


def current_season_year(started_at_by_year: Mapping[int, datetime | None]) -> int | None:
    """Año oficial de la temporada actual: la más reciente que ya empezó, o `None` si ninguna."""
    started = [year for year, started_at in started_at_by_year.items() if started_at is not None]
    return max(started, default=None)


def keep_started_at(current: datetime | None, match_started_at: datetime | None) -> datetime | None:
    """Inicio de una temporada tras ver empezar (o no) uno de sus partidos.

    El primer inicio se conserva para siempre: ni un partido posterior lo mueve ni
    una cancelación lo borra (RF-123).
    """
    return current if current is not None else match_started_at
