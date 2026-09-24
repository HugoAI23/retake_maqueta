"""T-091 · K/D calculado (C-12; RF-79 de la 002 revisado)."""

from decimal import Decimal

import pytest

from app.domain.kd import kd_of


@pytest.mark.parametrize(("published", "kills", "deaths", "expected"), [
    (None, 10, 8, Decimal("1.25")),
    (None, 2, 3, Decimal("0.67")),      # 0,666… se redondea a 2 decimales
    (None, 1, 8, Decimal("0.13")),      # 0,125 redondea hacia arriba
    (None, 7, 0, Decimal("7")),         # con 0 deaths, K/D = kills
    (None, 0, 0, Decimal("0")),
    (None, None, 8, None),              # sin kills, ausente
    (None, 10, None, None),             # sin deaths, ausente
    (Decimal("1.5"), 10, 10, Decimal("1.5")),  # un K/D publicado manda sobre el calculado
    (Decimal("0.9"), None, None, Decimal("0.9")),
])
def test_kd(published, kills, deaths, expected):
    assert kd_of(published, kills, deaths) == expected
