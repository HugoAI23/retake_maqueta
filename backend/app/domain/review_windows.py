"""Revisión de los partidos finalizados (spec 003: RF-19 a RF-21; cambio C-25).

Un partido se consulta una vez al finalizar (o al registrarse ya finalizado) y después a las 24,
48 y 72 horas; si ya llevaba más de 3 días jugado cuando se registró como finalizado, solo esa
primera vez. Fuera de esos plazos, solo si el administrador lo pide.
"""

from datetime import datetime

from app.domain.vocabulary import FINISHED_REVIEW_AGE_LIMIT, FINISHED_REVIEW_INTERVAL, FINISHED_REVIEWS


def review_due(first_checked_at: datetime | None, reviews_done: int, now: datetime) -> bool:
    """Indica si toca consultar un partido finalizado.

    Args:
        first_checked_at: Cuándo se hizo la consulta al finalizar (RF-19), o `None` si aún no.
        reviews_done: Revisiones diarias ya hechas (RF-20).
        now: Hora actual (reloj inyectado).
    """
    if first_checked_at is None:
        return True
    if reviews_done >= FINISHED_REVIEWS:
        return False
    return now >= first_checked_at + (reviews_done + 1) * FINISHED_REVIEW_INTERVAL


def reviews_after_first_check(started_at: datetime | None, checked_at: datetime) -> int:
    """Revisiones que se dan por hechas tras la consulta al finalizar (RF-20).

    Todas, si el partido ya llevaba más de 3 días jugado: su plazo de correcciones ya pasó (por
    ejemplo, en la primera carga de una temporada). Ninguna, si es reciente o no se sabe su inicio.
    """
    if started_at is not None and checked_at - started_at > FINISHED_REVIEW_AGE_LIMIT:
        return FINISHED_REVIEWS
    return 0
