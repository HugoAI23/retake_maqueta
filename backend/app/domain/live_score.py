"""Marcador en vivo más avanzado (spec 003: RF-57 a RF-59).

Mientras un partido está en vivo, no manda la prioridad de fuentes (RF-67 de la 002)
sino el marcador más avanzado de cualquier fuente, y ese marcador nunca retrocede.
Al finalizar, el marcador final vuelve a seguir la prioridad de fuentes.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from app.domain.priority import SOURCE_PRIORITY


@dataclass(frozen=True)
class LiveScore:
    """Marcador de un partido en vivo.

    Attributes:
        maps_won: Mapas ganados por cada equipo; su suma es el número de mapas terminados.
        live_score: Puntos, rondas u overloads de cada equipo en el mapa en curso, o `None`
            si la fuente no lo publica (RF-90 de la 002).
    """

    maps_won: tuple[int, int]
    live_score: tuple[int, int] | None = None


@dataclass(frozen=True)
class SourceScore:
    """Marcador en vivo que publica una fuente."""

    source: str
    score: LiveScore


def advancement(score: LiveScore) -> tuple[int, int]:
    """Clave de avance (RF-58): mapas terminados y, a igualdad, lo sumado en el mapa en curso.

    Un marcador del mapa en curso ausente vale menos que cualquiera publicado, incluido 0-0.
    """
    in_progress = sum(score.live_score) if score.live_score is not None else -1
    return (sum(score.maps_won), in_progress)


def most_advanced(
    candidates: Iterable[SourceScore],
    registered: LiveScore | None,
    order: Sequence[str] = SOURCE_PRIORITY,
) -> LiveScore | None:
    """Marcador a registrar mientras el partido está en vivo.

    - Gana el más avanzado de cualquier fuente (RF-57, RF-58).
    - Si dos fuentes dan el mismo avance con distinto reparto, manda la prioridad de fuentes.
    - Nunca se devuelve uno menos avanzado que el registrado (RF-59).

    Returns:
        El marcador ganador, el registrado si ninguno lo supera, o `None` si no hay ninguno.
    """
    ranked = sorted(
        candidates,
        key=lambda c: (advancement(c.score), -order.index(c.source) if c.source in order else -len(order)),
    )
    best = ranked[-1].score if ranked else None
    if best is None:
        return registered
    if registered is not None and advancement(registered) > advancement(best):
        return registered
    return best
