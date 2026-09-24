"""T-020 · Revisión de los partidos finalizados (RF-19 a RF-21; cambio C-25).

Una consulta al finalizar (RF-19) y otra a las 24, 48 y 72 horas (RF-20), salvo si el partido ya
llevaba más de 3 días jugado cuando se registró como finalizado.
"""

from datetime import UTC, datetime, timedelta

from app.domain.review_windows import review_due, reviews_after_first_check

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def test_sin_consultar_todavia_toca_la_consulta_al_finalizar():
    assert review_due(first_checked_at=None, reviews_done=0, now=NOW)


def test_las_revisiones_van_a_las_24_48_y_72_horas():
    first = NOW - timedelta(hours=23, minutes=59)
    assert not review_due(first, 0, NOW)
    assert review_due(NOW - timedelta(hours=24), 0, NOW)
    assert not review_due(NOW - timedelta(hours=47), 1, NOW)
    assert review_due(NOW - timedelta(hours=48), 1, NOW)
    assert review_due(NOW - timedelta(hours=72), 2, NOW)


def test_tras_tres_revisiones_no_se_vuelve_a_consultar():
    # RF-21: fuera de plazo solo a petición del administrador.
    assert not review_due(NOW - timedelta(days=30), 3, NOW)


def test_un_partido_reciente_empieza_sus_tres_revisiones():
    started = NOW - timedelta(hours=3)
    assert reviews_after_first_check(started_at=started, checked_at=NOW) == 0


def test_un_partido_que_ya_llevaba_mas_de_3_dias_jugado_no_se_revisa_mas():
    started = NOW - timedelta(days=3, minutes=1)
    assert reviews_after_first_check(started_at=started, checked_at=NOW) == 3


def test_sin_hora_de_inicio_se_revisa_como_uno_reciente():
    assert reviews_after_first_check(started_at=None, checked_at=NOW) == 0
