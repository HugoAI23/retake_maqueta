"""T-021 · Fases (RF-31, RF-134)."""

import pytest

from app.domain.phases import normalize_phase


@pytest.mark.parametrize(
    ("source_value", "expected"),
    [
        ("week", "week"),
        ("group", "group"),
        ("winners_bracket", "winners_bracket"),
        ("losers_bracket", "losers_bracket"),
        ("grand_final", "grand_final"),
        ("Winners Bracket", "winners_bracket"),
        ("grand-final", "grand_final"),
        ("  Group ", "group"),
    ],
)
def test_las_cinco_fases_se_reconocen(source_value, expected):
    assert normalize_phase(source_value) == expected


@pytest.mark.parametrize("source_value", ["play-in", "tiebreaker", "final", "", None])
def test_cualquier_otra_fase_queda_sin_fase(source_value):
    assert normalize_phase(source_value) is None
