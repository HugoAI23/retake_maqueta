"""Edades en UTC (RF-23, RF-108, RF-109; revisión R-2 de la spec y plan D-10).

La edad se calcula en el servidor con la fecha UTC y se entrega como un rango, para
que la fecha de nacimiento nunca salga del servidor (RF-24).
"""

from datetime import UTC, date, datetime
from typing import NamedTuple


class AgeRange(NamedTuple):
    """Edad en años cumplidos: `min == max` si es exacta; dos valores si solo se sabe el año."""

    min: int
    max: int


def _age_on(birth_date: date, today: date) -> int:
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)


def player_age(birth_date: date | None, birth_year: int | None, now: datetime) -> AgeRange | None:
    """Edad de un jugador en la fecha UTC de `now`.

    - Con fecha completa: edad exacta (RF-23).
    - Con solo el año, exacto o aproximado: las dos edades posibles (RF-108).
    - Sin datos: `None`.
    """
    today = now.astimezone(UTC).date()
    if birth_date is not None:
        age = _age_on(birth_date, today)
        return AgeRange(age, age)
    if birth_year is not None:
        return AgeRange(today.year - birth_year - 1, today.year - birth_year)
    return None


def approx_birth_year(age: int, observed_year: int) -> int:
    """Año de nacimiento aproximado a partir de una edad publicada sin fecha (RF-109)."""
    return observed_year - age
