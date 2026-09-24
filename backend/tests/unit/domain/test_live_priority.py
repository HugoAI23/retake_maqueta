"""T-023 · Partido prioritario cuando no caben todos los partidos en vivo (RF-23 a RF-26)."""

from datetime import UTC, datetime, timedelta

from app.domain.live_priority import LiveMatch, live_cycles, prioritary_match

T = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)
MIN = timedelta(minutes=1)


def test_si_caben_todos_se_consultan_todos_cada_60_segundos():
    matches = [LiveMatch("a", T), LiveMatch("b", T + MIN)]
    assert live_cycles(matches, pause=timedelta(seconds=2)) == {"a": timedelta(seconds=60), "b": timedelta(seconds=60)}


def test_si_no_caben_el_prioritario_cada_60_s_y_los_demas_cada_2_min():
    matches = [LiveMatch("tarde", T + 90 * MIN), LiveMatch("temprano", T), LiveMatch("medio", T + 30 * MIN)]
    # Con 20 s de pausa: 1 listado + 3 partidos = 4 consultas = 80 s > 60 s.
    cycles = live_cycles(matches, pause=timedelta(seconds=20))
    assert cycles == {"temprano": timedelta(seconds=60), "medio": timedelta(minutes=2), "tarde": timedelta(minutes=2)}


def test_sin_spec_del_spotlight_manda_el_que_empezo_antes():
    matches = [LiveMatch("b", T + MIN), LiveMatch("a", T)]
    assert prioritary_match(matches) == "a"


def test_con_spec_del_spotlight_manda_el_que_destaca():
    matches = [LiveMatch("a", T), LiveMatch("b", T + MIN)]
    assert prioritary_match(matches, spotlight_id="b") == "b"
    # Si el destacado ya no está en vivo, se vuelve a la regla de la hora de inicio.
    assert prioritary_match(matches, spotlight_id="z") == "a"


def test_empate_de_hora_de_inicio_con_desempate_estable():
    matches = [LiveMatch("m2", T), LiveMatch("m1", T)]
    assert prioritary_match(matches) == prioritary_match(list(reversed(matches))) == "m1"


def test_sin_partidos_en_vivo():
    assert live_cycles([], pause=timedelta(seconds=2)) == {}
    assert prioritary_match([]) is None
