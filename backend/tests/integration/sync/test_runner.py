"""T-051 · Pruebas del ejecutor de consultas sync/runner.py (RF-22, RF-43 a RF-47, RF-141 a RF-146)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.curation.loader import Curation
from app.db.models import DatasetChange, Incident, Match, SourceState, SyncRun
from app.sources.contract import ConsultaResult, Rejection
from app.sync.planner import PlannedQuery
from app.sync.runner import execute_consultation

from tests.integration.ingest.helpers import rec, season_and_event, team

T0 = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)


def _sample_records(source_id="m100", status="scheduled"):
    return [
        *season_and_event(),
        *team("4", "[FICTICIO] OpTic Texas"),
        *team("743", "[FICTICIO] Gentle Mates"),
        rec("match", source_id, event_ref="bp:ev1", status=status, scheduled_at="2026-12-05T20:00:00Z", best_of=5),
    ]


def test_consulta_con_exito_ingesta_y_actualiza_estado(session):
    """RF-22: Una consulta con éxito ingesta datos, anota estado, sync_run y avisa de cambios."""
    records = _sample_records("m100")
    result = ConsultaResult(
        source="bp",
        job="regular",
        outcome="success",
        records=records,
        seen=["bp:m100"],
        item_count=1,
    )
    notified = []

    res_report = execute_consultation(
        session,
        result=result,
        curation=Curation(),
        now=T0,
        notify_fn=lambda changed: notified.extend(changed),
    )

    # Ingest report returned
    assert res_report.accepted > 0

    # SourceState updated
    state = session.get(SourceState, ("bp", "regular"))
    assert state is not None
    assert state.last_attempt_at == T0
    assert state.last_success_at == T0
    assert state.last_item_count == 1

    # SyncRun recorded
    run = session.scalar(select(SyncRun).where(SyncRun.job == "regular"))
    assert run is not None
    assert run.outcome == "success"

    # DatasetChange and notify called
    assert len(notified) > 0
    for ds in notified:
        dc = session.get(DatasetChange, ds)
        assert dc is not None
        assert dc.last_changed_at == T0


def test_consulta_fallida_conserva_datos_y_no_frena_a_otras(session):
    """RF-43, RF-44, RF-141: Una consulta fallida conserva datos existentes y anota la incidencia."""
    # Primero insertamos un partido
    init_records = _sample_records("m100")
    execute_consultation(
        session,
        result=ConsultaResult(source="bp", job="regular", outcome="success", records=init_records, item_count=1),
        curation=Curation(),
        now=T0,
    )

    # Ahora una consulta fallida (error 503)
    t_fail = T0 + timedelta(minutes=1)
    fail_result = ConsultaResult(
        source="bp",
        job="regular",
        outcome="failure",
        message="503 Service Unavailable",
    )
    execute_consultation(session, result=fail_result, curation=Curation(), now=t_fail)

    # El partido anterior se conserva intacto (RF-43)
    matches = session.scalars(select(Match)).all()
    assert len(matches) == 1

    # SourceState: last_attempt se actualiza pero last_success NO
    state = session.get(SourceState, ("bp", "regular"))
    assert state.last_attempt_at == t_fail
    assert state.last_success_at == T0

    # SyncRun anota el fallo y hay incidencia en el registro (RF-141)
    runs = session.scalars(select(SyncRun).where(SyncRun.outcome == "failure")).all()
    assert len(runs) == 1
    assert "503" in runs[0].message

    inc = session.scalar(select(Incident).where(Incident.kind == "query_failed"))
    assert inc is not None
    assert "503" in inc.reason


def test_respuesta_vacia_donde_antes_habia_datos_cuenta_como_fallo(session):
    """RF-46: Si una fuente responde vacía cuando antes tenía datos, se trata como fallo."""
    # Primer estado: tenía 10 elementos
    state = SourceState(source="bp", job="regular", last_attempt_at=T0, last_success_at=T0, last_item_count=10)
    session.add(state)
    session.commit()

    t_empty = T0 + timedelta(minutes=5)
    empty_result = ConsultaResult(
        source="bp",
        job="regular",
        outcome="success",
        records=[],
        seen=[],
        item_count=0,
    )

    execute_consultation(session, result=empty_result, curation=Curation(), now=t_empty)

    # Debe haberse tratado como fallo (RF-46)
    run = session.scalar(select(SyncRun).where(SyncRun.finished_at == t_empty))
    assert run is not None
    assert run.outcome == "failure"
    assert "RF-46" in run.message

    # last_success_at no se actualizó
    updated_state = session.get(SourceState, ("bp", "regular"))
    assert updated_state.last_success_at == T0


def test_consulta_prohibida_se_anota_como_incidencia_query_forbidden(session):
    """RF-42, RF-143: Una consulta prohibida por las normas de la fuente anota incidencia query_forbidden."""
    forbidden_result = ConsultaResult(
        source="bp",
        job="regular",
        outcome="forbidden",
        message="Robots.txt prohíbe esta ruta",
    )
    execute_consultation(session, result=forbidden_result, curation=Curation(), now=T0)

    run = session.scalar(select(SyncRun))
    assert run.outcome == "forbidden"

    inc = session.scalar(select(Incident).where(Incident.kind == "query_forbidden"))
    assert inc is not None
    assert "Robots.txt" in inc.reason


def test_consulta_con_datos_rechazados_queda_parcial_y_registra_incidencias(session):
    """RF-47, RF-105, RF-142: Un resultado con datos rechazados pasa a parcial y registra incidencias data_rejected."""
    records = _sample_records("m100")
    rej = Rejection(ref="bp:p99", field="player", reason="Estructura no válida", value_excerpt="bad_json")
    result = ConsultaResult(
        source="bp",
        job="regular",
        outcome="success",
        records=records,
        rejected=[rej],
        item_count=2,
    )

    execute_consultation(session, result=result, curation=Curation(), now=T0)

    run = session.scalar(select(SyncRun))
    assert run.outcome == "partial"

    inc = session.scalar(select(Incident).where(Incident.kind == "data_rejected"))
    assert inc is not None
    assert inc.subject == "bp:p99:player"
    assert inc.reason == "Estructura no válida"


def test_partido_desaparecido_registra_incidencia_match_disappeared(session):
    """RF-50, RF-144: Si un partido lleva 24 h sin aparecer en consultas con éxito, se registra match_disappeared."""
    # Insertar el partido visto en T0
    records = _sample_records("m_desaparece")
    execute_consultation(
        session,
        result=ConsultaResult(source="bp", job="regular", outcome="success", records=records, seen=["bp:m_desaparece"], item_count=1),
        curation=Curation(),
        now=T0,
    )

    # 25 horas después, otra consulta con éxito que NO incluye al partido
    t_25h = T0 + timedelta(hours=25)
    execute_consultation(
        session,
        result=ConsultaResult(source="bp", job="regular", outcome="success", records=_sample_records("otro"), seen=["bp:otro"], item_count=1),
        curation=Curation(),
        now=t_25h,
    )

    # Debe haberse anotado una incidencia match_disappeared
    inc = session.scalar(select(Incident).where(Incident.kind == "match_disappeared"))
    assert inc is not None
    assert "desaparecido" in inc.reason.lower()


def test_run_query_con_cliente_educado_y_transporte_simulado(session, clock):
    """T-051: run_query invoca al conector según la consulta planificada y ejecuta el flujo completo."""
    from app.sources import bp
    from app.sources.http import PoliteClient
    from app.sources.simulated import simulated_transport
    from app.sync.runner import run_query

    transport = simulated_transport("partido_en_vivo", clock, "test")
    client = PoliteClient("bp", transport=transport, clock=clock, sleep=lambda s: None, base_url=bp.BASE_URL)

    query = PlannedQuery(job="regular", source="bp")
    report = run_query(session, query=query, client=client, curation=Curation(), now=T0)

    assert report.accepted > 0
    state = session.get(SourceState, ("bp", "regular"))
    assert state is not None
    assert state.last_success_at == T0


# --- Revisión de F5: el ejecutor según la documentación (plan §5; RF-46, RF-50, RF-142, RF-146) ---


def test_una_ficha_de_equipo_no_toca_el_estado_del_listado(session):
    # Las fichas de equipo del "Resto" no son un listado: no cambian la base de RF-46 ni el reloj del ciclo.
    listing = ConsultaResult(source="bp", job="regular", outcome="success", records=_sample_records("m1"),
                             seen=["bp:m1"], item_count=290)
    execute_consultation(session, result=listing, curation=Curation(), now=T0)
    team_page = ConsultaResult(source="bp", job="regular", outcome="success", records=[], item_count=None)
    execute_consultation(session, result=team_page, curation=Curation(), now=T0 + timedelta(minutes=2), follow_up=True)
    state = session.get(SourceState, ("bp", "regular"))
    assert (state.last_item_count, state.last_attempt_at) == (290, T0)


def test_la_lista_de_proximos_puede_quedar_vacia_sin_ser_un_fallo(session):
    # RF-46 es para los listados completos; la lista de próximos se vacía al acabar la jornada.
    for minute, count in ((0, 2), (1, 0)):
        execute_consultation(session, result=ConsultaResult(source="bp", job="pre_match", outcome="success",
                                                            records=[], item_count=count),
                             curation=Curation(), now=T0 + timedelta(minutes=minute))
    assert [run.outcome for run in session.scalars(select(SyncRun).order_by(SyncRun.id))] == ["success", "success"]


def test_la_desaparicion_solo_cuenta_las_consultas_que_listan_partidos(session):
    # RF-50: 24 h sin aparecer en consultas con éxito que listan partidos; el detalle de otro partido no cuenta.
    execute_consultation(session, result=ConsultaResult(source="bp", job="regular", outcome="success",
                                                        records=_sample_records("m1"), seen=["bp:m1"], item_count=1),
                         curation=Curation(), now=T0)
    execute_consultation(session, result=ConsultaResult(source="bp", job="live", outcome="success",
                                                        records=[], seen=["bp:otro"], item_count=1),
                         curation=Curation(), now=T0 + timedelta(hours=25))
    assert session.scalar(select(Incident).where(Incident.kind == "match_disappeared")) is None
    assert session.scalars(select(Match)).one().disappeared_at is None


def test_la_discrepancia_de_cancelacion_se_anota_con_su_partido_y_su_motivo(session):
    records = [*_sample_records("m1"),
               rec("match", "M1", source="wiki", event_ref="bp:ev1", best_of=5, status="cancelled", same_as=["bp:m1"])]
    execute_consultation(session, result=ConsultaResult(source="bp", job="regular", outcome="success", records=records,
                                                        item_count=1), curation=Curation(), now=T0)
    incident = session.scalar(select(Incident).where(Incident.kind == "cancel_discrepancy"))
    assert (incident.subject, incident.reason) == ("bp:m1", "cancelación publicada solo por wiki")


def test_un_pais_sin_traducir_se_anota_con_el_jugador_y_el_numero(session):
    records = [rec("player", "p1", gamertag="[FICTICIO] Uno", country="bp:99")]
    execute_consultation(session, result=ConsultaResult(source="bp", job="regular", outcome="success", records=records,
                                                        item_count=1), curation=Curation(), now=T0)
    incident = session.scalar(select(Incident).where(Incident.kind == "data_rejected"))
    assert (incident.subject, incident.reason) == ("bp:p1", "país de BreakingPoint sin traducir: 99")


def test_cada_consulta_del_plan_usa_su_consulta_del_conector(monkeypatch):
    # Plan §5: listado completo en la carga inicial y el "Resto"; solo la lista antes del partido y en vivo;
    # la página del partido en vivo y en la revisión; las fichas de cada equipo tras el listado.
    from app.sources import bp
    from app.sync.runner import consult

    calls = []
    ok = lambda job: ConsultaResult(source="bp", job=job, outcome="success")  # noqa: E731
    guests = {"744"}
    # Los invitados conocidos llegan a los dos listados, que no vuelven a pedir su ficha (RF-18b, plan I-38).
    monkeypatch.setattr(bp, "consult_regular", lambda client, now, job, known_guests: calls.append(("regular", job, known_guests is guests)) or ok(job))
    monkeypatch.setattr(bp, "consult_upcoming", lambda client, now, job, known_guests: calls.append(("upcoming", job, known_guests is guests)) or ok(job))
    monkeypatch.setattr(bp, "consult_match", lambda client, mid, now, job: calls.append(("match", job, mid)) or ok(job))
    monkeypatch.setattr(bp, "consult_teams", lambda client, ids, season, now, job, guests: calls.append(("teams", job, tuple(ids), season, set(guests))) or ok(job))
    season = (2026, "2025-10-28", "2026-10-29")
    for query in (PlannedQuery("initial_load", "bp"), PlannedQuery("regular", "bp"), PlannedQuery("pre_match", "bp"),
                  PlannedQuery("live", "bp"), PlannedQuery("live", "bp", match_id="900"),
                  PlannedQuery("finished_matches", "bp", match_id="901"),
                  PlannedQuery("regular", "bp", team_id="4", season=season),
                  PlannedQuery("regular", "bp", team_id="744", season=season, guest=True)):
        consult(query, client=None, now=T0, known_guests=guests)
    assert calls == [("regular", "initial_load", True), ("regular", "regular", True), ("upcoming", "pre_match", True),
                     ("upcoming", "live", True),
                     ("match", "live", "900"), ("match", "finished_matches", "901"), ("teams", "regular", ("4",), season, set()),
                     ("teams", "regular", ("744",), season, {"744"})]


def test_un_roster_de_un_equipo_ajeno_a_la_cdl_no_deja_la_consulta_parcial(session):
    """RF-18c (C-26): se descarta sin anotarlo; la consulta sale bien y el registro queda limpio."""
    records = [*_sample_records("m100"), rec("player", "p1", gamertag="[FICTICIO] Uno"),
               rec("roster", "2026/858/p1", season_year=2026, franchise_ref="bp:858", player_ref="bp:p1")]
    result = ConsultaResult(source="bp", job="regular", outcome="success", records=records, item_count=1)
    execute_consultation(session, result=result, curation=Curation(), now=T0)
    assert session.scalar(select(SyncRun)).outcome == "success"
    assert session.scalar(select(Incident)) is None
