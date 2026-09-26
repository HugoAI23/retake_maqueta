"""T-005 de la spec 004 · Balance de series y mapas de la temporada (RF-136 a RF-139 de la 002, C-29)."""

import pytest

from app.domain.season_balance import Balance, FinishedMatch, Record, counts, season_balances

A, B, C = "a", "b", "c"
GUEST = "invitado"


def played(side_1, side_2, winner=None, maps=(None, None)):
    return FinishedMatch(sides=(side_1, side_2), winner_side=winner, maps_won=maps)


def test_la_serie_suma_una_ganada_al_ganador_y_una_perdida_al_rival():
    balances = season_balances([A, B], [played(A, B, winner=2, maps=(1, 3))], season_has_matches=True)
    assert balances[A].series == Record(won=0, lost=1)
    assert balances[B].series == Record(won=1, lost=0)


def test_los_mapas_suman_los_propios_como_ganados_y_los_del_rival_como_perdidos():
    # RF-137: un 3–1 suma 3 ganados y 1 perdido.
    balances = season_balances([A, B], [played(A, B, winner=1, maps=(3, 1))], season_has_matches=True)
    assert balances[A].maps == Record(won=3, lost=1)
    assert balances[B].maps == Record(won=1, lost=3)


def test_se_acumulan_todos_los_partidos_de_la_temporada():
    matches = [
        played(A, B, winner=1, maps=(3, 1)),
        played(C, A, winner=1, maps=(3, 2)),
        played(B, C, winner=2, maps=(0, 3)),
    ]
    balances = season_balances([A, B, C], matches, season_has_matches=True)
    assert balances[A] == Balance(series=Record(1, 1), maps=Record(5, 4))
    assert balances[B] == Balance(series=Record(0, 2), maps=Record(1, 6))
    assert balances[C] == Balance(series=Record(2, 0), maps=Record(6, 2))


def test_sin_ganador_pero_con_marcador_gana_el_lado_con_mas_mapas():
    # Decisión D-5 del plan.
    balances = season_balances([A, B], [played(A, B, maps=(2, 3))], season_has_matches=True)
    assert balances[A] == Balance(series=Record(0, 1), maps=Record(2, 3))
    assert balances[B] == Balance(series=Record(1, 0), maps=Record(3, 2))


def test_sin_ganador_y_con_marcador_empatado_cuentan_los_mapas_y_no_la_serie():
    balances = season_balances([A, B], [played(A, B, maps=(1, 1))], season_has_matches=True)
    assert balances[A] == Balance(series=Record(0, 0), maps=Record(1, 1))


def test_con_ganador_y_sin_marcador_cuenta_la_serie_y_no_los_mapas():
    # RF-138: p. ej., una victoria por incomparecencia.
    balances = season_balances([A, B], [played(A, B, winner=1)], season_has_matches=True)
    assert balances[A] == Balance(series=Record(1, 0), maps=Record(0, 0))
    assert balances[B] == Balance(series=Record(0, 1), maps=Record(0, 0))


def test_un_marcador_a_medias_no_es_un_marcador():
    balances = season_balances([A, B], [played(A, B, winner=1, maps=(3, None))], season_has_matches=True)
    assert balances[A] == Balance(series=Record(1, 0), maps=Record(0, 0))


def test_sin_ganador_ni_marcador_no_cuenta():
    # RF-138a.
    balances = season_balances([A, B], [played(A, B)], season_has_matches=True)
    assert balances[A] == Balance(series=Record(0, 0), maps=Record(0, 0))
    assert balances[B] == Balance(series=Record(0, 0), maps=Record(0, 0))


def test_los_partidos_contra_invitados_cuentan_para_el_equipo_de_la_liga():
    # RF-136; el invitado no está en la tabla (RF-117c de la 002), así que no tiene balance.
    matches = [played(GUEST, A, winner=2, maps=(1, 3)), played(A, GUEST, winner=2, maps=(2, 3))]
    balances = season_balances([A], matches, season_has_matches=True)
    assert balances == {A: Balance(series=Record(1, 1), maps=Record(5, 4))}


def test_un_lado_sin_equipo_no_impide_contar_el_otro():
    balances = season_balances([A], [played(A, None, winner=1, maps=(3, 0))], season_has_matches=True)
    assert balances[A] == Balance(series=Record(1, 0), maps=Record(3, 0))


def test_un_equipo_sin_partidos_queda_en_cero():
    balances = season_balances([A, B, C], [played(A, B, winner=1, maps=(3, 0))], season_has_matches=True)
    assert balances[C] == Balance(series=Record(0, 0), maps=Record(0, 0))


def test_con_partidos_registrados_pero_ninguno_finalizado_todos_quedan_en_cero():
    balances = season_balances([A, B], [], season_has_matches=True)
    assert balances == {A: Balance(Record(0, 0), Record(0, 0)), B: Balance(Record(0, 0), Record(0, 0))}


def test_sin_ningun_partido_en_la_temporada_el_balance_no_esta_disponible():
    # RF-139 y decisión D-6: los partidos de la temporada todavía no se han obtenido.
    assert season_balances([A, B], [], season_has_matches=False) is None


@pytest.mark.parametrize(("match", "expected"), [
    (played(A, B, winner=1, maps=(3, 1)), True),
    (played(A, B, winner=1), True),            # solo la serie (RF-138)
    (played(A, B, maps=(1, 1)), True),         # solo los mapas
    (played(A, B, maps=(3, None)), False),     # marcador a medias y sin ganador
    (played(A, B), False),                     # RF-138a
])
def test_un_partido_cuenta_si_suma_a_la_serie_o_a_los_mapas(match, expected):
    # Los partidos que cuentan fijan la última actualización de la fila (RF-53e de la 004, D-7).
    assert counts(match) is expected
