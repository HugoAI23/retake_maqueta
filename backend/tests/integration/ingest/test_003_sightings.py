"""T-039 · Partidos desaparecidos y reaparecidos (spec 003: RF-50 a RF-52)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.models import ExternalRef, Match
from app.ingest.sightings import apply_sightings, detect_disappearances
from tests.integration.ingest.test_matches import base, match

T = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
H = timedelta(hours=1)


def get_match(session):
    session.expire_all()
    return session.scalars(select(Match)).one()


def test_referencias_vistas_en_una_consulta_con_exito(session, ingest):
    ingest([*base(), match(status="finished", maps_won=[3, 0], winner_side=1)])
    apply_sightings(session, ["bp:m1"], observed_at=T)
    ref = session.scalars(select(ExternalRef).where(ExternalRef.kind == "match")).one()
    assert ref.last_seen_at == T


def test_desaparece_tras_24_horas_y_se_conserva_tal_cual(session, ingest):
    ingest([*base(), match(status="live", maps_won=[1, 0])])
    apply_sightings(session, ["bp:m1"], observed_at=T)
    disappeared = detect_disappearances(session, {"bp": T + 24 * H}, now=T + 24 * H)
    m = get_match(session)
    assert disappeared == [m.id]
    assert m.disappeared_at == T + 24 * H
    # Se conserva tal como estaba, también en vivo (RF-51).
    assert (m.status, m.maps_won_1) == ("live", 1)


def test_una_fuente_caida_no_hace_desaparecer_nada(session, ingest):
    ingest([*base(), match(status="finished", maps_won=[3, 0], winner_side=1)])
    apply_sightings(session, ["bp:m1"], observed_at=T)
    # 30 h después, pero la última consulta con éxito de BreakingPoint es la que lo vio.
    assert detect_disappearances(session, {"bp": T}, now=T + 30 * H) == []
    assert get_match(session).disappeared_at is None


def test_no_se_anota_dos_veces(session, ingest):
    ingest([*base(), match(status="finished", maps_won=[3, 0], winner_side=1)])
    apply_sightings(session, ["bp:m1"], observed_at=T)
    assert detect_disappearances(session, {"bp": T + 25 * H}, now=T + 25 * H)
    assert detect_disappearances(session, {"bp": T + 26 * H}, now=T + 26 * H) == []


def test_reaparece_y_vuelve_a_actualizarse(session, ingest):
    ingest([*base(), match(status="live", maps_won=[1, 0])])
    apply_sightings(session, ["bp:m1"], observed_at=T)
    detect_disappearances(session, {"bp": T + 25 * H}, now=T + 25 * H)
    reappeared = apply_sightings(session, ["bp:m1"], observed_at=T + 26 * H)
    ingest([match(hours=30, status="finished", maps_won=[3, 1], winner_side=1)])
    m = get_match(session)
    assert reappeared == [m.id]
    assert m.disappeared_at is None and m.status == "finished"  # RF-52


def test_sin_referencias_vistas_nunca_no_hay_desaparicion(session, ingest):
    # Datos cargados sin consultas (p. ej. los datos de prueba de la 002): no se evalúan.
    ingest([*base(), match(status="finished", maps_won=[3, 0], winner_side=1)])
    assert detect_disappearances(session, {"bp": T + 100 * H}, now=T + 100 * H) == []
