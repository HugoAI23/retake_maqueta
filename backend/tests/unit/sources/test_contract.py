"""T-026 · Contrato del resultado de consulta y marca de campo ilegible."""

import pytest

from app.ingest.records import RecordError, parse_record
from app.sources.contract import MESSAGE_LIMIT, ConsultaResult, Rejection, plain_message


def test_mensaje_largo_se_recorta_a_500_caracteres_terminado_en_puntos_suspensivos():
    message = plain_message("x" * 800)
    assert len(message) == MESSAGE_LIMIT == 500
    assert message.endswith("…")


def test_mensaje_corto_se_deja_igual_y_los_saltos_de_linea_se_aplanan():
    assert plain_message("Error 503") == "Error 503"
    assert plain_message("  línea 1\n\nlínea 2\t ") == "línea 1 línea 2"
    assert plain_message(None) is None


def test_el_html_de_un_mensaje_se_conserva_como_texto_literal():
    # Texto plano (RF-119): no se interpreta; el frontend lo escapará al pintarlo.
    assert plain_message("<script>alert(1)</script>") == "<script>alert(1)</script>"


def test_resultado_de_consulta_con_sus_valores_por_defecto():
    result = ConsultaResult(source="bp", job="regular", outcome="success")
    assert (result.records, result.seen, result.rejected, result.message) == ([], [], [], None)


def test_resultado_rechaza_un_resultado_desconocido():
    with pytest.raises(ValueError):
        ConsultaResult(source="bp", job="regular", outcome="casi")


def test_parcial_si_hubo_rechazos():
    result = ConsultaResult(source="bp", job="regular", outcome="success",
                            rejected=[Rejection(ref="bp:1", field="kills", reason="formato no entendido")])
    assert result.with_rejections_outcome().outcome == "partial"


BASE = {"kind": "player", "source": "bp", "source_id": "27", "observed_at": "2026-09-23T12:00:00Z", "gamertag": "Shotzzy"}


def test_un_registro_puede_marcar_campos_ilegibles():
    record = parse_record({**BASE, "unreadable": ["country", "birth_date"]})
    assert record.unreadable == ["country", "birth_date"]
    assert parse_record(BASE).unreadable == []


def test_solo_se_pueden_marcar_como_ilegibles_campos_del_registro():
    with pytest.raises(RecordError, match="unreadable"):
        parse_record({**BASE, "unreadable": ["no_existe"]})
    with pytest.raises(RecordError, match="unreadable"):
        parse_record({**BASE, "unreadable": ["source_id"]})
