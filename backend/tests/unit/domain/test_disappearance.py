"""T-021 · Partidos desaparecidos de las fuentes (RF-50, RF-90)."""

from datetime import UTC, datetime, timedelta

from app.domain.disappearance import Sighting, is_disappeared, is_missing_live

T0 = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
H = timedelta(hours=1)


def test_desaparece_tras_24_horas_sin_aparecer_en_ninguna_consulta_con_exito():
    assert is_disappeared([Sighting("bp", last_seen_at=T0, last_success_at=T0 + 24 * H)])


def test_con_menos_de_24_horas_de_ausencia_comprobada_no_desaparece():
    assert not is_disappeared([Sighting("bp", last_seen_at=T0, last_success_at=T0 + 23 * H)])


def test_una_consulta_fallida_no_cuenta_como_no_aparecer():
    # La fuente lleva 30 h fallando: la última consulta con éxito aún lo incluía.
    assert not is_disappeared([Sighting("bp", last_seen_at=T0, last_success_at=T0)])


def test_si_alguna_de_las_fuentes_que_lo_publicaban_aun_lo_ve_no_desaparece():
    sightings = [
        Sighting("bp", last_seen_at=T0, last_success_at=T0 + 30 * H),
        Sighting("wiki", last_seen_at=T0 + 29 * H, last_success_at=T0 + 30 * H),
    ]
    assert not is_disappeared(sightings)


def test_sin_fuentes_que_lo_publicaran_no_se_puede_decir_que_desapareciera():
    assert not is_disappeared([])


def test_en_vivo_se_da_por_perdido_a_los_60_segundos():
    assert is_missing_live([Sighting("bp", last_seen_at=T0, last_success_at=T0 + timedelta(seconds=60))])
    assert not is_missing_live([Sighting("bp", last_seen_at=T0, last_success_at=T0 + timedelta(seconds=59))])
