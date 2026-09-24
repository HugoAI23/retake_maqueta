"""T-019 · Identidad combinada campo a campo (RF-61 a RF-63)."""

from datetime import UTC, datetime

from app.domain.identities import IdentityData
from app.domain.identity_merge import SourceIdentity, identity_changed, merge_identities

T1 = datetime(2026, 3, 1, tzinfo=UTC)
T3 = datetime(2026, 3, 3, tzinfo=UTC)


def test_cada_campo_sale_de_la_fuente_con_mas_prioridad_que_lo_publica():
    merged = merge_identities([
        SourceIdentity("wiki", short_name="FaZe Vegas", abbreviation="FAZE", logo_url="https://w/logo.png",
                       primary_color="#E43D30", secondary_color="#000000", valid_from=T3),
        SourceIdentity("bp", short_name="FaZe Vegas", abbreviation="VGS", logo_url=None,
                       primary_color="#E43D30", secondary_color=None, valid_from=T1),
    ])
    # BreakingPoint manda donde publica; donde no, la Wiki completa el campo.
    assert merged.data == IdentityData("FaZe Vegas", "VGS", "https://w/logo.png", "#E43D30", "#000000")
    # La fecha de vigencia es un campo más: manda BreakingPoint (Q-45).
    assert merged.valid_from == T1


def test_sin_fecha_de_vigencia_publicada_queda_nula():
    merged = merge_identities([SourceIdentity("bp", short_name="OpTic Texas", abbreviation="TX")])
    assert merged.valid_from is None


def test_sin_ninguna_identidad_no_hay_resultado():
    assert merge_identities([]) is None


def test_un_cambio_solo_en_una_fuente_secundaria_no_produce_identidad_nueva():
    before = merge_identities([
        SourceIdentity("bp", short_name="OpTic Texas", abbreviation="TX", primary_color="#93C852"),
        SourceIdentity("wiki", short_name="OpTic Texas", abbreviation="OPTIC", primary_color="#93C852"),
    ])
    after = merge_identities([
        SourceIdentity("bp", short_name="OpTic Texas", abbreviation="TX", primary_color="#93C852"),
        SourceIdentity("wiki", short_name="OpTic Gaming Texas", abbreviation="OTX", primary_color="#00FF00"),
    ])
    assert not identity_changed(before.data, after.data)


def test_un_cambio_en_el_resultado_combinado_si_produce_identidad_nueva():
    before = merge_identities([SourceIdentity("bp", short_name="Atlanta FaZe", abbreviation="ATL")])
    after = merge_identities([SourceIdentity("bp", short_name="FaZe Vegas", abbreviation="VGS")])
    assert identity_changed(before.data, after.data)
    assert identity_changed(None, after.data)


def test_solo_cambia_la_fecha_de_vigencia_no_es_identidad_nueva():
    a = merge_identities([SourceIdentity("bp", short_name="G2 Minnesota", valid_from=T1)])
    b = merge_identities([SourceIdentity("bp", short_name="G2 Minnesota", valid_from=T3)])
    assert not identity_changed(a.data, b.data)


def test_los_valores_no_validos_no_cuentan():
    merged = merge_identities([
        SourceIdentity("bp", short_name="Boston Breach", logo_url="javascript:alert(1)", invalid_fields={"logo_url"}),
        SourceIdentity("wiki", short_name="Boston Breach", logo_url="https://w/bos.png"),
    ])
    assert merged.data.logo_url == "https://w/bos.png"
