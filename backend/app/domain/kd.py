"""K/D de un jugador en un mapa (cambio C-12 de la spec 003; RF-79 de la 002 revisado).

Ninguna fuente publica hoy el K/D (H-3 de F0), así que se calcula. Es una excepción a RF-45
de la 002 ("sin métricas derivadas").
"""

from decimal import ROUND_HALF_UP, Decimal

TWO_DECIMALS = Decimal("0.01")


def kd_of(published: Decimal | None, kills: int | None, deaths: int | None) -> Decimal | None:
    """K/D que se registra.

    Args:
        published: K/D publicado por alguna fuente; si existe, manda sobre el calculado.
        kills: Bajas del jugador en el mapa, o `None` si no se conocen.
        deaths: Muertes del jugador en el mapa, o `None` si no se conocen.

    Returns:
        El K/D publicado; si no hay, kills ÷ deaths redondeado a 2 decimales (mitad hacia
        arriba); con 0 deaths, K/D = kills; si falta kills o deaths, `None` (ausente).
    """
    if published is not None:
        return published
    if kills is None or deaths is None:
        return None
    if deaths == 0:
        return Decimal(kills)
    return (Decimal(kills) / Decimal(deaths)).quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)
