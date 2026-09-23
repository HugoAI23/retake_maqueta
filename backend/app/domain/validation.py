"""Valores imposibles (RF-100, RF-101) y logos aceptables (RF-130).

Un valor no válido no se registra: se guarda como observación no válida y el dato
se trata como ausente (plan §3.3). Aquí solo se decide si un valor es válido; una
ausencia (`None`) no es "no válida", es otra cosa y se trata en el valor resuelto.
"""

from decimal import Decimal
from numbers import Real
from urllib.parse import urlparse

# Extensiones de imagen aceptadas para un logo (plan D-15).
IMAGE_EXTENSIONS = (".png", ".svg", ".jpg", ".jpeg", ".webp", ".gif")


def _is_number(value: object) -> bool:
    """Número real, excluidos los booleanos (en Python `True` es un entero)."""
    return isinstance(value, (Real, Decimal)) and not isinstance(value, bool)


def is_valid_non_negative(value: object) -> bool:
    """Estadística, marcador, K/D o premio: debe ser un número mayor o igual que 0 (RF-101).

    El 0 es válido: significa "no lo hizo", no "no se sabe" (RF-65).
    """
    return _is_number(value) and value >= 0


def is_valid_pool_percent(value: object) -> bool:
    """Porcentaje de la bolsa: número entre 0 y 100, ambos incluidos (RF-101)."""
    return _is_number(value) and 0 <= value <= 100


def maps_needed_to_win(best_of: int) -> int:
    """Mapas necesarios para ganar un partido al mejor de N: ⌊N/2⌋ + 1."""
    return best_of // 2 + 1


def is_valid_maps_won(value: object, best_of: int) -> bool:
    """Mapas ganados por un equipo: entre 0 y los necesarios para ganar (RF-101)."""
    return is_valid_non_negative(value) and value <= maps_needed_to_win(best_of)


def is_valid_logo_url(value: object) -> bool:
    """Logo: dirección `https` con servidor y con extensión de imagen (RF-130, plan D-15).

    Así nunca se acepta como logo algo que el navegador pudiera ejecutar
    (`javascript:`, páginas HTML, datos incrustados).
    """
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.path.lower().endswith(IMAGE_EXTENSIONS)
    )
