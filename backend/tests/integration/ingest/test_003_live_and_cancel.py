"""T-040 y T-041 · Marcador en vivo más avanzado (RF-57 a RF-59) y cancelación por prioridad (RF-53)."""

from sqlalchemy import select

from app.db.models import Match
from tests.integration.ingest.helpers import rec
from tests.integration.ingest.test_matches import base, match


def wiki_match(hours=0, **fields):
    fields.setdefault("best_of", 5)
    return rec("match", "M1", source="wiki", hours=hours, event_ref="bp:ev1", same_as=["bp:m1"], **fields)


def get_match(session):
    session.expire_all()
    return session.scalars(select(Match)).one_or_none()


def scores(m):
    return (m.maps_won_1, m.maps_won_2, m.live_score_1, m.live_score_2)


# --- T-040 --------------------------------------------------------------------------------------


def test_en_vivo_manda_el_marcador_mas_avanzado_aunque_sea_de_una_fuente_secundaria(session, ingest):
    ingest([*base(), match(status="live", maps_won=[1, 1], live_map={"mode": "Hardpoint", "score": [100, 80]}),
            wiki_match(status="live", maps_won=[2, 1], live_map={"mode": "Search & Destroy", "score": [0, 0]})])
    assert scores(get_match(session)) == (2, 1, 0, 0)


def test_en_vivo_el_marcador_nunca_retrocede(session, ingest):
    ingest([*base(), match(status="live", maps_won=[2, 1], live_map={"mode": "Hardpoint", "score": [40, 30]})])
    ingest([match(hours=1, status="live", maps_won=[1, 1], live_map={"mode": "Hardpoint", "score": [240, 200]})])
    assert scores(get_match(session)) == (2, 1, 40, 30)
    ingest([match(hours=2, status="live", maps_won=[2, 2], live_map={"mode": "Overload", "score": [0, 1]})])
    assert scores(get_match(session)) == (2, 2, 0, 1)


def test_al_finalizar_el_marcador_final_vuelve_a_seguir_la_prioridad(session, ingest):
    ingest([*base(), match(status="live", maps_won=[2, 2]), wiki_match(status="live", maps_won=[2, 3])])
    ingest([match(hours=1, status="finished", maps_won=[3, 2], winner_side=1),
            wiki_match(hours=1, status="finished", maps_won=[2, 3], winner_side=2)])
    m = get_match(session)
    assert (m.maps_won_1, m.maps_won_2, m.winner_side) == (3, 2, 1)  # manda BreakingPoint (RF-67 de la 002)


# --- T-041 --------------------------------------------------------------------------------------


def test_una_cancelacion_de_la_fuente_principal_borra_el_partido(session, ingest):
    ingest([*base(), match(status="scheduled"), wiki_match(status="scheduled")])
    ingest([match(hours=1, status="cancelled")])
    assert get_match(session) is None


def test_una_cancelacion_solo_de_una_fuente_secundaria_no_borra_el_partido(session, ingest):
    ingest([*base(), match(status="scheduled"), wiki_match(status="scheduled")])
    report = ingest([wiki_match(hours=1, status="cancelled")])
    m = get_match(session)
    assert m is not None and m.status == "scheduled"
    assert [d.reason for d in report.discrepancies] == ["cancelación publicada solo por wiki"]
    assert report.discrepancies[0].ref == "bp:m1"
