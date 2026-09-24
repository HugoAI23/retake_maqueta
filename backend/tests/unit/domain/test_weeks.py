"""T-092 · Semana calculada de los clasificatorios (C-13; RF-31 de la 002 revisado).

Fechas ancla de la muestra real de la Wiki de F0 (`MatchSchedule`, consultada el 2026-09-23; la muestra
se retiró con I-26):
2025-12-05 21:30 UTC es "Week 1" y 2026-01-18 20:00 UTC es "Week 4". Las semanas 2 y 3 son
fechas de prueba; entre ellas va el parón navideño (dos semanas sin partidos).
"""

from datetime import UTC, datetime

from app.domain.weeks import week_numbers


def utc(*args):
    return datetime(*args, tzinfo=UTC)


WEEK_1 = utc(2025, 12, 5, 21, 30)   # muestra: "Week 1"
WEEK_2 = utc(2025, 12, 13, 19, 0)
WEEK_3 = utc(2026, 1, 10, 19, 0)    # tras el parón navideño
WEEK_4 = utc(2026, 1, 18, 20, 0)    # muestra: "Week 4"


def test_orden_de_las_semanas_con_partidos_incluido_el_paron_navideno():
    weeks = week_numbers({"a": WEEK_1, "b": WEEK_2, "c": WEEK_3, "d": WEEK_4, "e": utc(2025, 12, 7, 22, 0)})
    assert weeks == {"a": 1, "b": 2, "c": 3, "d": 4, "e": 1}


def test_la_semana_va_de_lunes_a_domingo_en_hora_de_ciudad_de_mexico():
    sunday_night_mx = utc(2025, 12, 8, 3, 0)   # lunes en UTC, domingo 21:00 en Ciudad de México
    monday_mx = utc(2025, 12, 8, 7, 0)         # lunes 01:00 en Ciudad de México
    assert week_numbers({"a": WEEK_1, "b": sunday_night_mx, "c": monday_mx}) == {"a": 1, "b": 1, "c": 2}


def test_un_partido_sin_fecha_no_tiene_semana():
    assert week_numbers({"a": WEEK_1, "b": None}) == {"a": 1, "b": None}


def test_sin_partidos():
    assert week_numbers({}) == {}
