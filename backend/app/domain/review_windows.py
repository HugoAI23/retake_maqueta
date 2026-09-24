"""Revisión de los partidos finalizados (spec 003: RF-19 a RF-21).

Un partido finalizado se consulta cada hora mientras tenga "Estadísticas pendientes" y
durante 7 días desde que las tiene todas; después solo si el administrador lo pide.
"""

from datetime import datetime

from app.domain.vocabulary import REVIEW_WINDOW


def needs_review(status: str, stats_complete_at: datetime | None, now: datetime) -> bool:
    """Indica si un partido entra en la revisión horaria de partidos finalizados.

    Args:
        status: Estado del partido en Retake.
        stats_complete_at: Cuándo tuvo todas sus estadísticas registradas, o `None` si aún
            le faltan. Un partido sin mapas (forfeit) lo tiene desde que finaliza (T-046).
        now: Hora actual (reloj inyectado).

    Returns:
        `True` durante la ventana `[stats_complete_at, stats_complete_at + 7 días)` o mientras
        falten estadísticas. Los partidos no finalizados tienen sus propios ciclos: `False`.
    """
    if status != "finished":
        return False
    if stats_complete_at is None:
        return True
    return now < stats_complete_at + REVIEW_WINDOW
