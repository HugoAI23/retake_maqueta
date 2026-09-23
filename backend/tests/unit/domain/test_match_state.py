"""T-022 · Estado de un partido (RF-35, RF-62, RF-63, RF-81 a RF-83; plan §3.4)."""

import pytest

from app.domain.match_state import apply_source_status


@pytest.mark.parametrize(
    ("source_status", "expected"),
    [("scheduled", "scheduled"), ("live", "live"), ("finished", "finished")],
)
def test_estados_directos(source_status, expected):
    assert apply_source_status(None, source_status).status == expected


def test_aplazado_sigue_programado():
    result = apply_source_status("scheduled", "postponed")
    assert result.status == "scheduled"
    assert result.postponed


def test_forfeit_pasa_a_finalizado():
    result = apply_source_status("scheduled", "forfeit")
    assert result.status == "finished"
    assert result.forfeit


def test_cancelado_se_borra():
    result = apply_source_status("live", "cancelled")
    assert result.cancelled
    assert result.status is None


@pytest.mark.parametrize(
    ("current", "source_status"),
    [("finished", "live"), ("finished", "scheduled"), ("live", "scheduled"), ("live", "postponed")],
)
def test_un_partido_nunca_retrocede(current, source_status):
    assert apply_source_status(current, source_status).status == current


def test_puede_saltarse_un_estado_hacia_delante():
    assert apply_source_status("scheduled", "finished").status == "finished"


def test_empieza_cuando_llega_a_en_vivo_o_mas_alla_sin_forfeit():
    assert apply_source_status("scheduled", "live").started
    assert apply_source_status(None, "finished").started
    assert not apply_source_status("scheduled", "scheduled").started
    assert not apply_source_status("scheduled", "forfeit").started
    assert not apply_source_status("scheduled", "cancelled").started


def test_estado_de_fuente_desconocido_es_un_error():
    with pytest.raises(ValueError):
        apply_source_status(None, "paused")
