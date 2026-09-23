"""Prioridad entre fuentes (RF-66, RF-67, RF-75, RF-110).

El valor resuelto de un campo es el valor válido de la fuente con más prioridad.
Un valor nulo o no válido no cuenta: cede ante el de la siguiente fuente (RF-100).
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

# Regla general (RF-67): BreakingPoint.gg > Call of Duty Esports Wiki > web oficial de la CDL.
SOURCE_PRIORITY: tuple[str, ...] = ("bp", "wiki", "cdl")

# Tabla de posiciones (RF-75): web oficial de la CDL > BreakingPoint.gg > Wiki.
STANDINGS_PRIORITY: tuple[str, ...] = ("cdl", "bp", "wiki")


@dataclass(frozen=True)
class SourceValue:
    """Lo que una fuente publica para un campo.

    Attributes:
        source: `bp`, `wiki` o `cdl`.
        value: Valor publicado; `None` si la fuente lo publica como ausente.
        is_valid: `False` si la validación lo descartó (RF-100).
        last_seen_at: Cuándo se observó por última vez; desempata dos valores de la misma
            fuente (una entidad puede tener varias referencias de la misma fuente).
    """

    source: str
    value: object
    is_valid: bool = True
    last_seen_at: datetime | None = None


def choose(values: Iterable[SourceValue], order: Sequence[str] = SOURCE_PRIORITY) -> SourceValue | None:
    """Devuelve la observación ganadora (con su fuente y su fecha), o `None` si no hay ninguna válida."""
    candidates = [v for v in values if v.is_valid and v.value is not None and v.source in order]
    if not candidates:
        return None

    def rank(candidate: SourceValue) -> tuple:
        # Primero la fuente con más prioridad; dentro de ella, la observación más reciente.
        recency = candidate.last_seen_at.timestamp() if candidate.last_seen_at else float("-inf")
        return (order.index(candidate.source), -recency)

    return min(candidates, key=rank)


def resolve(values: Iterable[SourceValue], order: Sequence[str] = SOURCE_PRIORITY) -> object:
    """Devuelve el valor resuelto de un campo, o `None` si ninguna fuente tiene un valor válido."""
    winner = choose(values, order)
    return None if winner is None else winner.value
