"""T-022 · Frescura de los datos y fuentes paradas (RF-89, RF-114)."""

from datetime import UTC, datetime, timedelta

from app.domain.freshness import is_source_stopped, is_stale, shortest_cycle, stale_threshold

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
S = timedelta(seconds=1)


def test_umbral_por_conjunto_de_datos():
    assert stale_threshold("live") == 60 * S
    for dataset in ("matches", "standings", "franchises", "players", "events", "championships", "season"):
        assert stale_threshold(dataset) == timedelta(hours=1)


def test_datos_en_vivo_sin_actualizar_a_partir_de_60_segundos():
    assert not is_stale("live", last_success_at=NOW - 60 * S, now=NOW)
    assert is_stale("live", last_success_at=NOW - 61 * S, now=NOW)


def test_resto_de_datos_sin_actualizar_a_partir_de_una_hora():
    assert not is_stale("standings", last_success_at=NOW - timedelta(minutes=59), now=NOW)
    assert is_stale("standings", last_success_at=NOW - timedelta(hours=1, seconds=1), now=NOW)


def test_sin_ninguna_consulta_con_exito_aun_no_hay_datos_que_avisar():
    assert not is_stale("matches", last_success_at=None, now=NOW)


def test_ciclo_mas_corto_de_cada_fuente_segun_haya_partidos_en_vivo():
    assert shortest_cycle("bp", live_active=True) == 60 * S
    assert shortest_cycle("bp", live_active=False) == timedelta(hours=1)
    # La Wiki no aporta datos en vivo (plan I-3): su ciclo más corto es siempre 1 h.
    assert shortest_cycle("wiki", live_active=True) == timedelta(hours=1)


def test_fuente_parada_si_pasa_mas_del_doble_de_su_ciclo_sin_consultas():
    assert not is_source_stopped("bp", last_attempt_at=NOW - 120 * S, now=NOW, live_active=True)
    assert is_source_stopped("bp", last_attempt_at=NOW - 121 * S, now=NOW, live_active=True)
    # Al acabar el partido en vivo, el ciclo pasa a 1 h: 5 min sin consultas ya no es una parada.
    assert not is_source_stopped("bp", last_attempt_at=NOW - timedelta(minutes=5), now=NOW, live_active=False)
    assert is_source_stopped("bp", last_attempt_at=NOW - timedelta(hours=2, seconds=1), now=NOW, live_active=False)


def test_una_fuente_que_nunca_se_ha_consultado_esta_parada():
    assert is_source_stopped("bp", last_attempt_at=None, now=NOW, live_active=False)


def test_la_wiki_nunca_esta_parada_porque_no_tiene_ciclo():
    # Spec 003, C-19: sus datos llegan por la importación manual de archivos (RF-4, RF-114).
    assert not is_source_stopped("wiki", last_attempt_at=None, now=NOW, live_active=False)
    assert not is_source_stopped("wiki", last_attempt_at=NOW - timedelta(days=400), now=NOW, live_active=False)
