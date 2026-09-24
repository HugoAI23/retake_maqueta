"""C-24 · Fichas de los equipos invitados: al aparecer y después una vez al mes (spec 003: RF-18b; plan I-38)."""

from datetime import timedelta

from sqlalchemy import select

from app.db.models import ExternalRef, Franchise
from app.sources.contract import ConsultaResult
from tests.integration.ingest.helpers import rec, season_and_event, team
from tests.integration.sync.test_worker import T0, Recorder, make_worker

SEASON = (2026, "2025-10-28", "2026-10-29")


def listing_records():
    return [
        *season_and_event(),
        *team("4", "[FICTICIO] OpTic Texas"),
        rec("franchise", "744", guest=True),
        rec("identity", "744#identity", franchise_ref="bp:744", short_name="[FICTICIO] Huntsmen"),
        rec("match", "m1", event_ref="bp:ev1", best_of=5, status="finished", scheduled_at="2026-01-09T20:00:00Z",
            slots=[{"franchise_ref": "bp:4"}, {"franchise_ref": "bp:744"}], maps_won=[3, 0], winner_side=1),
    ]


def result(query):
    if query.team_id is None:
        return ConsultaResult(source="bp", job=query.job, outcome="success", records=listing_records(),
                              seen=["bp:m1"], item_count=1, teams=("4",), season=SEASON)
    return ConsultaResult(source="bp", job=query.job, outcome="success", item_count=None)


def run_ticks(worker, session, start, count):
    for step in range(count):
        worker.tick(session=session, now=start + timedelta(seconds=5 * step))


def guest_checked_at(session):
    session.expire_all()
    franchise_id = session.scalar(select(ExternalRef.entity_id).where(
        ExternalRef.kind == "franchise", ExternalRef.source == "bp", ExternalRef.source_id == "744"))
    return session.get(Franchise, franchise_id).guest_checked_at


def test_la_ficha_de_un_invitado_nuevo_se_pide_tras_el_listado(session, clock):
    recorder = Recorder(result)
    worker = make_worker(session, clock, recorder)
    run_ticks(worker, session, T0, 3)
    assert [(q.team_id, q.guest) for q in recorder.queries] == [(None, False), ("4", False), ("744", True)]
    assert guest_checked_at(session) == T0 + timedelta(seconds=10)


def test_despues_se_pide_una_vez_al_mes(session, clock):
    recorder = Recorder(result)
    worker = make_worker(session, clock, recorder)
    run_ticks(worker, session, T0, 3)

    # Los listados de cada hora no vuelven a pedirla dentro del mes...
    recorder.queries.clear()
    run_ticks(worker, session, T0 + timedelta(days=29), 3)
    assert ("744", True) not in [(q.team_id, q.guest) for q in recorder.queries]

    # ...y pasado el mes, sí.
    recorder.queries.clear()
    run_ticks(worker, session, T0 + timedelta(days=30, hours=1), 3)
    assert ("744", True) in [(q.team_id, q.guest) for q in recorder.queries]


def test_una_ficha_de_invitado_que_falla_se_vuelve_a_pedir_en_el_siguiente_listado(session, clock):
    def failing(query):
        if query.guest:
            return ConsultaResult(source="bp", job=query.job, outcome="failure", message="HTTP 503")
        return result(query)

    recorder = Recorder(failing)
    worker = make_worker(session, clock, recorder)
    run_ticks(worker, session, T0, 3)
    assert guest_checked_at(session) is None
    recorder.queries.clear()
    run_ticks(worker, session, T0 + timedelta(hours=1, minutes=1), 3)
    assert ("744", True) in [(q.team_id, q.guest) for q in recorder.queries]


def test_el_listado_no_vuelve_a_pedir_los_invitados_ya_conocidos(session, clock):
    # El trabajador pasa al conector los invitados que ya están en la base (RF-18b).
    worker = make_worker(session, clock, Recorder(result))
    run_ticks(worker, session, T0, 1)
    worker.tick(session=session, now=T0 + timedelta(seconds=5))
    assert worker.known_guests == {"744"}
