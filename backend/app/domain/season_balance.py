"""Balance de series y mapas de la temporada (RF-136 a RF-139 de la 002; cambio C-29 de la spec 004).

Se calcula al leer, a partir de los partidos `finalizado` de la temporada actual. Los partidos
contra invitados cuentan para el equipo de la liga; el invitado no está en la tabla, así que
no recibe balance (RF-117c de la 002).
"""

from collections.abc import Hashable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    """Ganados y perdidos (de series o de mapas)."""

    won: int = 0
    lost: int = 0


@dataclass(frozen=True)
class Balance:
    """Balance de una franquicia en la temporada."""

    series: Record
    maps: Record


@dataclass(frozen=True)
class FinishedMatch:
    """Resultado de un partido `finalizado`.

    Attributes:
        sides: Franquicia de cada lado (1 y 2), o `None` si el lado no tiene equipo.
        winner_side: Lado ganador (1 o 2), o `None` si no está registrado.
        maps_won: Marcador final (mapas ganados por cada lado); un valor `None` = sin marcador.
    """

    sides: tuple[Hashable | None, Hashable | None]
    winner_side: int | None
    maps_won: tuple[int | None, int | None]


def _winner(match: FinishedMatch, has_score: bool) -> int | None:
    """Lado ganador: el registrado o, si falta, el que ganó más mapas (decisión D-5 del plan)."""
    if match.winner_side in (1, 2):
        return match.winner_side
    if has_score and match.maps_won[0] != match.maps_won[1]:
        return 1 if match.maps_won[0] > match.maps_won[1] else 2
    return None


def counts(match: FinishedMatch) -> bool:
    """Si el partido suma a la serie o a los mapas de sus equipos (RF-136 a RF-138a de la 002)."""
    has_score = None not in match.maps_won
    return has_score or _winner(match, has_score) is not None


def season_balances(
    franchises: Iterable[Hashable],
    matches: Iterable[FinishedMatch],
    season_has_matches: bool,
) -> dict[Hashable, Balance] | None:
    """Balance de cada franquicia de la tabla de posiciones.

    Args:
        franchises: Franquicias de la tabla de posiciones de la temporada actual.
        matches: Partidos `finalizado` de la temporada actual.
        season_has_matches: Si la temporada actual tiene algún partido registrado, en cualquier estado.

    Returns:
        Por franquicia, sus series y mapas ganados y perdidos (`0–0` si no ha jugado), o `None`
        (no disponible) si la temporada todavía no tiene ningún partido registrado (RF-139, D-6).
    """
    if not season_has_matches:
        return None
    totals = {franchise: [0, 0, 0, 0] for franchise in franchises}  # series +/-, mapas +/-
    for match in matches:
        has_score = None not in match.maps_won
        winner = _winner(match, has_score)
        for index, franchise in enumerate(match.sides):
            if franchise not in totals:
                continue  # invitado o lado sin equipo
            side = index + 1
            if winner is not None:
                totals[franchise][0 if winner == side else 1] += 1
            if has_score:
                totals[franchise][2] += match.maps_won[index]
                totals[franchise][3] += match.maps_won[1 - index]
    return {franchise: Balance(series=Record(sw, sl), maps=Record(mw, ml))
            for franchise, (sw, sl, mw, ml) in totals.items()}
