"""T-027 · Edades en UTC (RF-23, RF-108, RF-109)."""

from datetime import UTC, date, datetime

from app.domain.ages import AgeRange, approx_birth_year, player_age

TODAY = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


def test_fecha_completa_da_una_edad_exacta():
    assert player_age(date(2000, 5, 1), None, TODAY) == AgeRange(26, 26)


def test_el_dia_del_cumpleanos_ya_cuenta_y_el_dia_anterior_no():
    assert player_age(date(2000, 9, 22), None, TODAY) == AgeRange(26, 26)
    assert player_age(date(2000, 9, 23), None, TODAY) == AgeRange(25, 25)


def test_29_de_febrero_en_un_anio_no_bisiesto():
    feb_28 = datetime(2026, 2, 28, 12, 0, tzinfo=UTC)
    march_1 = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    assert player_age(date(2004, 2, 29), None, feb_28) == AgeRange(21, 21)
    assert player_age(date(2004, 2, 29), None, march_1) == AgeRange(22, 22)


def test_solo_el_anio_da_dos_edades_consecutivas():
    assert player_age(None, 2002, TODAY) == AgeRange(23, 24)


def test_la_fecha_completa_manda_sobre_el_anio():
    assert player_age(date(2002, 1, 1), 1990, TODAY) == AgeRange(24, 24)


def test_sin_datos_no_hay_edad():
    assert player_age(None, None, TODAY) is None


def test_edad_publicada_24_en_2026_da_anio_aproximado_2002():
    assert approx_birth_year(24, observed_year=2026) == 2002


def test_la_fecha_se_toma_en_utc():
    # 22-09-2026 a las 05:00 UTC: en Ciudad de México (UTC-6) aún es el 21 a las 23:00,
    # pero manda la fecha UTC (revisión R-2), así que el cumpleaños ya cuenta.
    late_21_mexico = datetime(2026, 9, 22, 5, 0, tzinfo=UTC)
    assert player_age(date(2000, 9, 22), None, late_21_mexico) == AgeRange(26, 26)
