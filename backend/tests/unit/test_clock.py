"""Pruebas del reloj inyectable (T-007)."""

from datetime import UTC, datetime

import pytest

from app.clock import FixedClock


def test_el_reloj_fijo_devuelve_el_instante_indicado(clock):
    assert clock.now() == datetime(2026, 9, 22, 12, 0, tzinfo=UTC)
    clock.set(datetime(2027, 1, 1, tzinfo=UTC))
    assert clock.now().year == 2027


def test_el_reloj_fijo_exige_zona_horaria():
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 9, 22))
