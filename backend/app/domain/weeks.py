"""Semana de los partidos de clasificatorio (cambio C-13 de la spec 003; RF-31 de la 002 revisado).

BreakingPoint no publica la semana (H-5 de F0), así que se calcula: es el orden de la semana
(de lunes a domingo, hora de Ciudad de México) entre las semanas con partidos del evento. Las
semanas sin partidos, como el parón navideño, no cuentan. Es una excepción a RF-45 de la 002.
"""

from collections.abc import Hashable, Mapping
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.vocabulary import SUMMARY_TIMEZONE

MEXICO_CITY = ZoneInfo(SUMMARY_TIMEZONE)


def _monday(moment: datetime) -> date:
    local = moment.astimezone(MEXICO_CITY).date()
    return local - timedelta(days=local.weekday())


def week_numbers[K: Hashable](dates: Mapping[K, datetime | None]) -> dict[K, int | None]:
    """Número de semana de cada partido de un evento.

    Args:
        dates: Fecha y hora de inicio de cada partido de fase `week` del evento, o `None` si
            no se conoce.

    Returns:
        Para cada partido, el orden (desde 1) de su semana entre las semanas con partidos;
        `None` si no tiene fecha.
    """
    mondays = sorted({_monday(moment) for moment in dates.values() if moment is not None})
    order = {monday: position for position, monday in enumerate(mondays, start=1)}
    return {key: order[_monday(moment)] if moment is not None else None for key, moment in dates.items()}
