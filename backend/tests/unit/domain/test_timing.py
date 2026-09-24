"""T-016 · Umbrales y ciclos de la spec 003, como constantes únicas."""

from datetime import timedelta

from app.domain import vocabulary as v


def test_ciclos_de_consulta():
    assert v.LIVE_CYCLE == timedelta(seconds=60)  # RF-16, RF-17
    assert v.SECONDARY_LIVE_CYCLE == timedelta(minutes=2)  # RF-24
    assert v.REST_CYCLE == timedelta(hours=1)  # RF-18 a RF-20
    assert v.PRE_MATCH_WINDOW == timedelta(hours=1)  # RF-17


def test_ciclos_de_la_pagina_y_umbrales_de_desactualizacion():
    assert (v.PAGE_CYCLE_LIVE, v.PAGE_CYCLE_REST) == (timedelta(seconds=30), timedelta(minutes=5))  # RF-80, RF-81
    assert (v.STALE_AFTER_LIVE, v.STALE_AFTER_REST) == (timedelta(seconds=60), timedelta(hours=1))  # RF-89


def test_plazos_de_revision_desaparicion_y_conservacion():
    # RF-19 y RF-20 (cambio C-25): tres revisiones, una al día, salvo partidos de hace más de 3 días.
    assert (v.FINISHED_REVIEWS, v.FINISHED_REVIEW_INTERVAL, v.FINISHED_REVIEW_AGE_LIMIT) == (
        3, timedelta(hours=24), timedelta(days=3))
    assert v.DISAPPEARED_AFTER == timedelta(hours=24)  # RF-50
    assert v.LIVE_MISSING_AFTER == timedelta(seconds=60)  # RF-90
    assert v.RETENTION == timedelta(days=7)  # RF-149, RF-154


def test_pausas_minimas_por_fuente():
    # Plan §1.2: 2 s en BreakingPoint y la CDL.
    # Spec 003, C-18: la Wiki no se consulta, así que no tiene pausa mínima (I-26).
    assert v.MIN_PAUSE == {"bp": timedelta(seconds=2), "cdl": timedelta(seconds=2)}
    assert set(v.MIN_PAUSE) == set(v.SOURCES) - {"wiki"}


def test_acceso_del_administrador_y_zona_del_resumen():
    assert v.SESSION_DURATION == timedelta(hours=8)  # RF-134
    assert (v.LOGIN_MAX_FAILURES, v.LOGIN_BLOCK) == (5, timedelta(minutes=15))  # RF-127
    assert v.SUMMARY_TIMEZONE == "America/Mexico_City"  # RF-150


def test_los_ciclos_de_la_pagina_son_mas_cortos_que_sus_umbrales():
    # Si no, el aviso de datos sin actualizar saltaría en páginas que funcionan bien.
    assert v.PAGE_CYCLE_LIVE < v.STALE_AFTER_LIVE and v.PAGE_CYCLE_REST < v.STALE_AFTER_REST
