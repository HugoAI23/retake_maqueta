"""T-053 · Pruebas del trabajador de sincronización (RF-9, RF-44, RF-100, RF-107, RF-136)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.curation.loader import Curation
from app.db.models import ExternalRef, Franchise, Incident, SourceState, SyncRequest, SyncRun
from app.sources.contract import ConsultaResult
from app.sync.planner import PlannedQuery
from app.sync.worker import SyncWorker, verify_production_safety
from tests.integration.ingest.helpers import rec, season_and_event, team

T0 = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)


def fake_consult(query, client, now):
    """Consulta simulada: el trabajador recibe la función de consulta en vez de un cliente trucado."""
    return ConsultaResult(
        source=query.source,
        job=query.job,
        outcome="success",
        records=[*season_and_event(), *team("4", "[FICTICIO] OpTic Texas"), *team("743", "[FICTICIO] Gentle Mates")],
        item_count=2,
    )


def make_worker(session, clock, consult_fn=fake_consult):
    return SyncWorker(engine=session.bind, client_factory=lambda s: None, consult_fn=consult_fn, clock=clock,
                      app_env="test", source_mode="simulated", curation_loader=lambda: Curation())


def test_se_niega_a_arrancar_en_produccion_con_modo_no_real(session):
    """RF-9: En producción se niega a arrancar si SOURCE_MODE no es 'real'."""
    with pytest.raises(RuntimeError, match="solo se admite SOURCE_MODE=real"):
        verify_production_safety(session, app_env="production", source_mode="simulated")


def test_se_niega_a_arrancar_en_produccion_con_datos_ficticios(session):
    """RF-9: En producción se niega a arrancar si la base de datos contiene datos [FICTICIO]."""
    from app.db.models import Identity
    fid = uuid.uuid4()
    session.add_all([
        Franchise(id=fid),
        Identity(
            id=uuid.uuid4(),
            franchise_id=fid,
            short_name="[FICTICIO] OpTic Texas",
            abbreviation="TX",
            valid_from=datetime(2025, 1, 1, tzinfo=UTC),
        ),
    ])
    session.commit()

    with pytest.raises(RuntimeError, match="datos ficticios"):
        verify_production_safety(session, app_env="production", source_mode="real")


def test_colas_por_fuente_aisladas(session, clock):
    """RF-44: Las consultas se reparten en colas por fuente, aisladas entre sí."""
    worker = make_worker(session, clock)

    q_bp = PlannedQuery(job="regular", source="bp")
    q_cdl = PlannedQuery(job="regular", source="cdl")

    worker.enqueue(q_bp)
    worker.enqueue(q_cdl)

    assert len(worker.queues["bp"]) == 1
    assert len(worker.queues["cdl"]) == 1


def test_recoge_peticion_del_administrador_y_la_ejecuta(session, clock):
    """RF-100, RF-104 a RF-106: Una petición sync_request pendiente se ejecuta y pasa a 'done' con su resultado."""
    req = SyncRequest(
        id=uuid.uuid4(),
        kind="source_refresh",
        source="bp",
        status="pending",
        requested_at=T0,
    )
    session.add(req)
    session.commit()

    worker = make_worker(session, clock)

    worker.tick(session=session, now=T0)

    saved = session.get(SyncRequest, req.id)
    assert saved.status == "done"
    assert saved.result == "success"
    assert saved.finished_at is not None


def test_una_sola_peticion_en_curso_por_fuente(session, clock):
    """RF-107: Solo se procesa una petición en curso por fuente a la vez; fuentes distintas avanzan en paralelo."""
    req_bp = SyncRequest(id=uuid.uuid4(), kind="source_refresh", source="bp", status="running", requested_at=T0, started_at=T0)
    req_cdl = SyncRequest(id=uuid.uuid4(), kind="source_refresh", source="cdl", status="pending", requested_at=T0)
    session.add_all([req_bp, req_cdl])
    session.commit()

    worker = make_worker(session, clock)
    worker.running_requests["bp"] = req_bp.id

    worker.process_sync_requests(session=session, now=T0)

    saved_cdl = session.get(SyncRequest, req_cdl.id)
    assert saved_cdl.status == "running"
    assert "cdl" in worker.running_requests


def test_peticion_wiki_se_rechaza_inmediatamente_como_prohibida(session, clock):
    """C-19, I-26: La petición de actualizar la Wiki se rechaza con resultado 'forbidden'."""
    req = SyncRequest(
        id=uuid.uuid4(),
        kind="source_refresh",
        source="wiki",
        status="pending",
        requested_at=T0,
    )
    session.add(req)
    session.commit()

    worker = make_worker(session, clock)
    worker.process_sync_requests(session=session, now=T0)

    saved = session.get(SyncRequest, req.id)
    assert saved.status == "done"
    assert saved.result == "forbidden"
    assert "import-wiki-csv" in saved.message


# --- Revisión de F5: el trabajador según la documentación (plan §5; RF-9 a RF-11, RF-16, RF-19 a RF-21) ---


def listing_done(session, now):
    """Estado de una fuente que ya hizo su carga inicial y su "Resto" a la hora `now`."""
    for job in ("initial_load", "regular"):
        session.add(SourceState(source="bp", job=job, last_attempt_at=now, last_success_at=now, last_item_count=2))
    session.commit()


class Recorder:
    def __init__(self, result=None, error=None):
        self.queries, self.result, self.error = [], result, error

    def __call__(self, query, client, now):
        self.queries.append(query)
        if self.error:
            raise self.error
        if self.result:
            return self.result(query)
        return ConsultaResult(source=query.source, job=query.job, outcome="success", item_count=1)


def test_en_modo_fixtures_el_proceso_no_arranca():
    # RF-9 a RF-11: con los datos de prueba no se consulta ninguna fuente, ni real ni simulada.
    from app.sync.worker import verify_source_mode

    with pytest.raises(RuntimeError, match="fixtures"):
        verify_source_mode("fixtures")
    verify_source_mode("simulated")
    verify_source_mode("real")


def test_en_produccion_arranca_con_datos_reales(session):
    verify_production_safety(session, app_env="production", source_mode="real")


def test_en_produccion_no_arranca_con_referencias_ficticias(session):
    session.add(ExternalRef(kind="player", source="bp", source_id="fx-1", fictional=True))
    session.commit()
    with pytest.raises(RuntimeError, match="datos ficticios"):
        verify_production_safety(session, app_env="production", source_mode="real")


def test_un_partido_terminado_se_revisa_una_vez_por_hora_y_no_en_cada_ciclo(session, clock):
    # RF-19: cada hora mientras tenga estadísticas pendientes (plan §5).
    ingest_finished(session)
    listing_done(session, T0)
    recorder = Recorder()
    worker = make_worker(session, clock, recorder)
    for seconds in (0, 5, 10, 60):
        worker.tick(session=session, now=T0 + timedelta(seconds=seconds))
    assert [(q.job, q.match_id) for q in recorder.queries] == [("finished_matches", "m1")]  # su id en BreakingPoint
    for seconds in (1, 6):  # a la hora también toca el "Resto", que va antes en la cola
        worker.tick(session=session, now=T0 + timedelta(hours=1, seconds=seconds))
    assert [q.job for q in recorder.queries] == ["finished_matches", "regular", "finished_matches"]


def test_lo_en_vivo_se_consulta_antes_que_la_cola_de_partidos_terminados(session, clock):
    # RF-16: el partido en vivo cada 60 s aunque haya muchos partidos terminados pendientes.
    listing_done(session, T0)
    recorder = Recorder()
    worker = make_worker(session, clock, recorder)
    for match_id in ("m1", "m2", "m3"):
        worker.enqueue(PlannedQuery("finished_matches", "bp", match_id=match_id))
    worker.enqueue(PlannedQuery("live", "bp", match_id="m9"))
    worker.tick(session=session, now=T0)
    assert (recorder.queries[0].job, recorder.queries[0].match_id) == ("live", "m9")


def test_tras_el_listado_se_consultan_las_fichas_de_cada_equipo(session, clock):
    # RF-18: el "Resto" incluye tabla, rosters y jugadores, que salen de las fichas de equipo.
    season = (2026, "2025-10-28", "2026-10-29")

    def result(query):
        if query.team_id is None:
            return ConsultaResult(source="bp", job=query.job, outcome="success", item_count=2, teams=("4", "743"),
                                  season=season)
        return ConsultaResult(source="bp", job=query.job, outcome="success", item_count=None)

    recorder = Recorder(result)
    worker = make_worker(session, clock, recorder)
    for seconds in (0, 5, 10):
        worker.tick(session=session, now=T0 + timedelta(seconds=seconds))
    assert [(q.job, q.team_id, q.season) for q in recorder.queries] == [
        ("initial_load", None, None), ("initial_load", "4", season), ("initial_load", "743", season)]
    assert session.get(SourceState, ("bp", "initial_load")).last_item_count == 2


def test_una_excepcion_en_una_consulta_se_anota_y_el_proceso_sigue(session, clock):
    listing_done(session, T0 - timedelta(hours=2))
    worker = make_worker(session, clock, Recorder(error=RuntimeError("fallo inesperado")))
    worker.tick(session=session, now=T0)
    run = session.scalars(select(SyncRun).where(SyncRun.outcome == "failure")).one()
    assert "fallo inesperado" in run.message
    assert session.scalar(select(Incident).where(Incident.kind == "query_failed")) is not None
    worker.consult_fn = Recorder()
    worker.tick(session=session, now=T0 + timedelta(hours=2))  # la sesión sigue utilizable


def test_la_limpieza_del_registro_es_cada_hora(session, clock, monkeypatch):
    # Plan §5: limpieza cada hora, no en cada ciclo de 5 s.
    calls = []
    monkeypatch.setattr("app.sync.worker.purge_old_entries", lambda s, now: calls.append(now) or 0)
    listing_done(session, T0)
    worker = make_worker(session, clock, Recorder())
    for seconds in (0, 5, 3601):
        worker.tick(session=session, now=T0 + timedelta(seconds=seconds))
    assert calls == [T0, T0 + timedelta(seconds=3601)]


def test_la_hora_de_un_partido_programado_es_la_ultima_publicada(session, clock):
    # RF-87 de la 002: manda la última fecha y hora de inicio.
    from app.ingest.pipeline import ingest_records

    ingest_records(session, [*season_and_event(), rec("match", "m1", event_ref="bp:ev1", best_of=5, status="scheduled",
                                                      scheduled_at="2026-12-06T20:00:00Z")], curation=Curation(), now=T0)
    ingest_records(session, [rec("match", "m1", hours=1, event_ref="bp:ev1", best_of=5, status="scheduled",
                                 scheduled_at="2026-12-05T20:30:00Z")], curation=Curation(), now=T0)
    session.commit()
    state = make_worker(session, clock).build_planner_state(session, T0)
    assert [m.scheduled_at for m in state.scheduled_matches] == [datetime(2026, 12, 5, 20, 30, tzinfo=UTC)]


def ingest_finished(session):
    from app.ingest.pipeline import ingest_records

    ingest_records(session, [*season_and_event(), rec("match", "m1", event_ref="bp:ev1", best_of=5, status="finished",
                                                      maps_won=[3, 1])], curation=Curation(), now=T0)
    session.commit()


def test_en_modo_simulado_el_reloj_empieza_a_la_hora_de_los_escenarios(session):
    # Con el reloj real, un partido del escenario (diciembre) nunca entraría en la ventana previa
    # de 1 h y `retake sync` no vería el en vivo (I-32).
    from app.sources.simulated import SCENARIO_START

    worker = SyncWorker(engine=session.bind, app_env="development", source_mode="simulated",
                        curation_loader=lambda: Curation())
    assert abs((worker.clock.now() - SCENARIO_START).total_seconds()) < 5
