"""T-019 · Prioridad entre fuentes (RF-66, RF-67, RF-75, RF-110)."""

from datetime import UTC, datetime

from app.domain.priority import SOURCE_PRIORITY, STANDINGS_PRIORITY, SourceValue, choose, resolve

T1 = datetime(2026, 9, 1, tzinfo=UTC)
T2 = datetime(2026, 9, 2, tzinfo=UTC)


def test_con_las_tres_fuentes_gana_breakingpoint():
    values = [SourceValue("cdl", "C"), SourceValue("wiki", "W"), SourceValue("bp", "B")]
    assert resolve(values) == "B"


def test_sin_breakingpoint_gana_la_wiki():
    assert resolve([SourceValue("cdl", "C"), SourceValue("wiki", "W")]) == "W"


def test_sin_breakingpoint_ni_wiki_gana_la_web_oficial():
    assert resolve([SourceValue("cdl", "C")]) == "C"


def test_un_valor_no_valido_de_la_fuente_principal_cede_ante_uno_valido():
    values = [SourceValue("bp", -3, is_valid=False), SourceValue("wiki", 3)]
    assert resolve(values) == 3


def test_un_valor_nulo_de_la_fuente_principal_cede_ante_otra():
    assert resolve([SourceValue("bp", None), SourceValue("wiki", "Mexico")]) == "Mexico"


def test_en_la_tabla_de_posiciones_manda_la_web_oficial():
    values = [SourceValue("bp", 200), SourceValue("wiki", 190), SourceValue("cdl", 210)]
    assert resolve(values, order=STANDINGS_PRIORITY) == 210
    assert resolve(values[:2], order=STANDINGS_PRIORITY) == 200


def test_sin_ningun_valor_valido_el_resultado_es_nulo():
    assert resolve([]) is None
    assert resolve([SourceValue("bp", -1, is_valid=False), SourceValue("cdl", None)]) is None


def test_cero_es_un_valor_y_no_cede():
    assert resolve([SourceValue("bp", 0), SourceValue("wiki", 5)]) == 0


def test_dos_valores_de_la_misma_fuente_gana_el_mas_reciente():
    values = [SourceValue("bp", "antiguo", last_seen_at=T1), SourceValue("bp", "nuevo", last_seen_at=T2)]
    assert resolve(values) == "nuevo"


def test_orden_de_prioridad_por_defecto():
    assert SOURCE_PRIORITY == ("bp", "wiki", "cdl")
    assert STANDINGS_PRIORITY == ("cdl", "bp", "wiki")


def test_choose_devuelve_la_observacion_ganadora_con_su_fuente_y_fecha():
    winner = choose([SourceValue("wiki", 24, last_seen_at=T1), SourceValue("cdl", 25, last_seen_at=T2)])
    assert winner == SourceValue("wiki", 24, last_seen_at=T1)
    assert choose([]) is None
