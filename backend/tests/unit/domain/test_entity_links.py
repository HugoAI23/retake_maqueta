"""T-020 · Quién es quién (RF-10, RF-18, RF-19, RF-113 a RF-115, RF-131 a RF-133)."""

import pytest

from app.domain.entity_links import CurationConflictError, group_refs

BP_1 = ("bp", "1")
WIKI_1 = ("wiki", "Player_One")
BP_2 = ("bp", "2")
WIKI_2 = ("wiki", "Player_Two")


def as_sets(groups):
    return {frozenset(group) for group in groups}


def test_mismo_gamertag_sin_enlace_son_dos_personas():
    # La función nunca mira nombres: dos referencias sin enlace quedan separadas.
    assert as_sets(group_refs([BP_1, BP_2])) == {frozenset({BP_1}), frozenset({BP_2})}


def test_un_enlace_declarado_por_una_fuente_une_las_referencias():
    groups = group_refs([BP_1, WIKI_1, BP_2], source_links=[(WIKI_1, BP_1)])
    assert as_sets(groups) == {frozenset({BP_1, WIKI_1}), frozenset({BP_2})}


def test_los_enlaces_son_transitivos():
    cdl = ("cdl", "x")
    groups = group_refs([BP_1, WIKI_1, cdl], source_links=[(BP_1, WIKI_1), (WIKI_1, cdl)])
    assert as_sets(groups) == {frozenset({BP_1, WIKI_1, cdl})}


def test_una_union_de_la_curacion_une_las_referencias():
    groups = group_refs([BP_1, BP_2], merges=[[BP_1, BP_2]])
    assert as_sets(groups) == {frozenset({BP_1, BP_2})}


def test_una_separacion_de_la_curacion_anula_un_enlace_de_fuente():
    groups = group_refs([BP_1, WIKI_1], source_links=[(BP_1, WIKI_1)], splits=[(BP_1, WIKI_1)])
    assert as_sets(groups) == {frozenset({BP_1}), frozenset({WIKI_1})}


def test_una_separacion_tambien_impide_uniones_indirectas():
    # BP_1–WIKI_1 y WIKI_1–BP_2 unirían BP_1 con BP_2, que la curación separa.
    groups = group_refs(
        [BP_1, WIKI_1, BP_2],
        source_links=[(BP_1, WIKI_1), (WIKI_1, BP_2)],
        splits=[(BP_1, BP_2)],
    )
    assert as_sets(groups) == {frozenset({BP_1, WIKI_1}), frozenset({BP_2})}


def test_unir_y_separar_las_mismas_referencias_es_un_conflicto_de_curacion():
    with pytest.raises(CurationConflictError):
        group_refs([BP_1, BP_2], merges=[[BP_1, BP_2]], splits=[(BP_1, BP_2)])


def test_franquicia_con_predecesora_es_la_misma():
    old = ("wiki", "Team_Old_City")
    new = ("wiki", "Team_New_City")
    assert as_sets(group_refs([old, new], source_links=[(new, old)])) == {frozenset({old, new})}


def test_franquicia_sin_predecesora_es_una_franquicia_nueva():
    old = ("wiki", "Team_Old_City")
    new = ("wiki", "Team_Fresh")
    assert as_sets(group_refs([old, new])) == {frozenset({old}), frozenset({new})}


def test_un_enlace_a_una_referencia_desconocida_la_incluye():
    groups = group_refs([BP_1], source_links=[(BP_1, WIKI_1)])
    assert as_sets(groups) == {frozenset({BP_1, WIKI_1})}


def test_el_resultado_no_depende_del_orden_de_entrada():
    links = [(BP_1, WIKI_1), (WIKI_1, BP_2)]
    splits = [(BP_1, BP_2)]
    first = as_sets(group_refs([BP_1, WIKI_1, BP_2], source_links=links, splits=splits))
    second = as_sets(group_refs([BP_2, WIKI_1, BP_1], source_links=list(reversed(links)), splits=splits))
    assert first == second
