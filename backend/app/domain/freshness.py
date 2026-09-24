"""Frescura de los datos y fuentes paradas (spec 003: RF-89, RF-112 a RF-114)."""

from datetime import datetime, timedelta

from app.domain.vocabulary import LIVE_CYCLE, REST_CYCLE, STALE_AFTER_LIVE, STALE_AFTER_REST

# Única fuente con datos en vivo tras la fase F0 (plan I-3).
LIVE_SOURCES = ("bp",)


def stale_threshold(dataset: str) -> timedelta:
    """Umbral de desactualización de un conjunto de datos: 60 s en vivo, 1 h el resto (RF-89)."""
    return STALE_AFTER_LIVE if dataset == "live" else STALE_AFTER_REST


def is_stale(dataset: str, last_success_at: datetime | None, now: datetime) -> bool:
    """Un conjunto está sin actualizar si su última consulta con éxito supera el umbral.

    Sin ninguna consulta con éxito todavía no hay datos que puedan estar desactualizados
    (por ejemplo, durante la carga inicial, RF-8): devuelve `False`.
    """
    if last_success_at is None:
        return False
    return now - last_success_at > stale_threshold(dataset)


def shortest_cycle(source: str, live_active: bool) -> timedelta:
    """Ciclo más corto vigente de una fuente: 60 s si consulta partidos en vivo, 1 h si no."""
    return LIVE_CYCLE if live_active and source in LIVE_SOURCES else REST_CYCLE


def is_source_stopped(source: str, last_attempt_at: datetime | None, now: datetime, live_active: bool) -> bool:
    """Fuente parada: más del doble de su ciclo más corto sin ninguna consulta (RF-114).

    Una fuente que nunca se ha consultado también está parada.
    """
    if last_attempt_at is None:
        return True
    return now - last_attempt_at > 2 * shortest_cycle(source, live_active)
