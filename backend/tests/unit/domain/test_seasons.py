"""T-023 · Temporada actual (RF-2, RF-3, RF-52, RF-53, RF-123)."""

from datetime import UTC, datetime

from app.domain.seasons import current_season_year, keep_started_at

T_2026 = datetime(2025, 12, 5, 18, 0, tzinfo=UTC)
T_2027 = datetime(2026, 12, 4, 18, 0, tzinfo=UTC)


def test_sin_temporadas_empezadas_no_hay_temporada_actual():
    assert current_season_year({2026: None, 2027: None}) is None
    assert current_season_year({}) is None


def test_2026_empezada_y_2027_no_la_actual_es_2026():
    assert current_season_year({2026: T_2026, 2027: None}) == 2026


def test_un_partido_de_qualifiers_de_2027_en_vivo_la_hace_actual():
    # El primer partido de 2027 (unos Qualifiers) pasa a en vivo: se fija su inicio.
    started_2027 = keep_started_at(None, T_2027)
    assert current_season_year({2026: T_2026, 2027: started_2027}) == 2027


def test_si_despues_se_cancela_ese_partido_sigue_siendo_2027():
    # El inicio nunca se borra: cancelar el partido no toca `started_at`.
    started_2027 = keep_started_at(None, T_2027)
    started_2027 = keep_started_at(started_2027, None)
    assert current_season_year({2026: T_2026, 2027: started_2027}) == 2027


def test_el_inicio_no_se_mueve_con_partidos_posteriores():
    later = datetime(2027, 1, 10, tzinfo=UTC)
    assert keep_started_at(T_2027, later) == T_2027
