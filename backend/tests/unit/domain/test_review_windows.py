"""T-020 · Ventanas de revisión de los partidos finalizados (RF-19 a RF-21)."""

from datetime import UTC, datetime, timedelta

from app.domain.review_windows import needs_review

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def test_con_estadisticas_pendientes_se_revisa_siempre():
    assert needs_review("finished", stats_complete_at=None, now=NOW)


def test_se_revisa_durante_7_dias_desde_que_se_completan():
    assert needs_review("finished", stats_complete_at=NOW - timedelta(days=6, hours=23), now=NOW)
    assert needs_review("finished", stats_complete_at=NOW, now=NOW)


def test_a_los_7_dias_exactos_deja_de_revisarse():
    assert not needs_review("finished", stats_complete_at=NOW - timedelta(days=7), now=NOW)
    assert not needs_review("finished", stats_complete_at=NOW - timedelta(days=30), now=NOW)


def test_un_forfeit_sin_mapas_tiene_sus_7_dias_desde_que_finaliza():
    # T-046 fija stats_complete_at al finalizar un partido sin mapas: la ventana es la misma.
    finished_at = NOW - timedelta(days=2)
    assert needs_review("finished", stats_complete_at=finished_at, now=NOW)


def test_los_partidos_no_finalizados_no_entran_en_esta_revision():
    # Tienen sus propios ciclos (en vivo, antes del partido o el resto cada hora).
    assert not needs_review("scheduled", stats_complete_at=None, now=NOW)
    assert not needs_review("live", stats_complete_at=None, now=NOW)
