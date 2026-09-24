"""Pruebas de integración del resumen diario (spec 003: RF-150 a RF-154; T-054).

- Totales y lista de incidencias distintas por fuente (RF-151, RF-152).
- Sin resumen si no hubo incidencias (RF-153).
- Generación al paso de medianoche de CDMX con reloj simulado (RF-150).
- Borrado a los 7 días (RF-154).
"""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from app.clock import FixedClock
from app.db.models import DailySummary, Incident, IncidentDay, SyncRun
from app.domain.vocabulary import SUMMARY_TIMEZONE
from app.sync.registry import purge_old_entries, record_incident, record_run
from app.sync.summary import generate_daily_summary
from app.sync.worker import SyncWorker


def test_dia_sin_incidencias_no_genera_resumen(session):
    """RF-153: Si un día natural termina sin ninguna incidencia, no se genera resumen."""
    day = date(2026, 9, 22)
    summary = generate_daily_summary(session, day=day)
    session.commit()

    assert summary is None
    row = session.get(DailySummary, day)
    assert row is None


def test_dia_con_incidencias_genera_resumen_completo(session):
    """RF-150 a RF-152: Resumen con totales por fuente, fallidas, rechazadas e incidencias."""
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    # 2026-09-22 15:00 CDMX
    instant = datetime(2026, 9, 22, 15, 0, tzinfo=tz).astimezone(UTC)
    day = date(2026, 9, 22)

    # 1. Registrar una consulta fallida en sync_run
    record_run(
        session,
        source="bp",
        job="regular",
        started_at=instant,
        finished_at=instant + timedelta(seconds=2),
        outcome="failure",
        message="HTTP 500",
    )

    # 2. Registrar incidencias para bp: una de consulta fallida y dos rechazos de datos (uno repetido)
    inc_fail = record_incident(
        session,
        kind="query_failed",
        subject="bp/regular",
        reason="HTTP 500 error",
        source="bp",
        now=instant,
    )
    inc_rej1 = record_incident(
        session,
        kind="data_rejected",
        subject="player/1",
        reason="Gamertag inválido",
        source="bp",
        value="bad_val",
        now=instant,
    )
    # Repetir el rechazo
    record_incident(
        session,
        kind="data_rejected",
        subject="player/1",
        reason="Gamertag inválido",
        source="bp",
        value="bad_val",
        now=instant + timedelta(minutes=5),
    )

    # 3. Registrar una incidencia para cdl: registro retenido
    inc_cdl = record_incident(
        session,
        kind="record_retained",
        subject="franchise/optic",
        reason="Franquicia sin asociar",
        source="cdl",
        now=instant,
    )

    session.commit()

    # Generar resumen para el día
    summary = generate_daily_summary(session, day=day, now=instant + timedelta(hours=8))
    session.commit()

    assert summary is not None
    assert summary.day == day
    content = summary.content

    # Comprobar estructura general y totales globales
    assert content["day"] == "2026-09-22"
    assert content["total_incidents"] == 4  # 1 fallida + 2 rechazos + 1 cdl
    assert content["total_failed_queries"] >= 1
    assert content["total_rejected_data"] == 2

    # Comprobar desglose por fuente
    sources = content["by_source"]
    assert "bp" in sources
    bp_data = sources["bp"]
    assert bp_data["failed_queries"] >= 1
    assert bp_data["rejected_data"] == 2
    assert bp_data["total_incidents"] == 3
    # Lista de incidencias distintas con repeticiones y acceso al registro (id)
    bp_incidents = bp_data["incidents"]
    assert len(bp_incidents) == 2  # 2 distintas
    rej_item = next(item for item in bp_incidents if item["id"] == inc_rej1.id)
    assert rej_item["kind"] == "data_rejected"
    assert rej_item["subject"] == "player/1"
    assert rej_item["repetitions"] == 2

    # Fuente CDL
    assert "cdl" in sources
    cdl_data = sources["cdl"]
    assert cdl_data["total_incidents"] == 1
    assert len(cdl_data["incidents"]) == 1
    assert cdl_data["incidents"][0]["id"] == inc_cdl.id
    assert cdl_data["incidents"][0]["repetitions"] == 1


def test_paso_de_medianoche_con_reloj_simulado(session):
    """RF-150: A las 00:00 de CDMX se genera automáticamente el resumen del día terminado."""
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    # Día 1: 2026-09-22 23:59:50 CDMX (05:59:50 UTC del día siguiente)
    dt_day1 = datetime(2026, 9, 22, 23, 59, 50, tzinfo=tz)
    sim_clock = FixedClock(dt_day1.astimezone(UTC))

    from app.db.models import SourceState

    session.add_all([
        SourceState(source="bp", job="initial_load", last_attempt_at=sim_clock.now(), last_success_at=sim_clock.now()),
        SourceState(source="bp", job="regular", last_attempt_at=sim_clock.now(), last_success_at=sim_clock.now()),
    ])
    record_incident(
        session,
        kind="data_rejected",
        subject="match/99",
        reason="Marcador imposible",
        source="bp",
        now=sim_clock.now(),
    )
    session.commit()

    worker = SyncWorker(
        engine=session.bind,
        clock=sim_clock,
        app_env="development",
        source_mode="simulated",
        client_factory=lambda src: None,
        curation_loader=lambda: None,
    )

    # Antes de medianoche: no se genera resumen
    worker.tick(session)
    session.commit()
    assert session.get(DailySummary, date(2026, 9, 22)) is None

    # Cruzar medianoche: 2026-09-23 00:00:05 CDMX
    dt_day2 = datetime(2026, 9, 23, 0, 0, 5, tzinfo=tz)
    sim_clock.set(dt_day2.astimezone(UTC))

    worker.tick(session)
    session.commit()

    # Se ha generado el resumen del día 22
    summary = session.get(DailySummary, date(2026, 9, 22))
    assert summary is not None
    assert summary.content["total_incidents"] == 1


def test_paso_de_medianoche_sin_incidencias(session):
    """RF-153: Si el día anterior no tuvo incidencias, al cruzar medianoche no se crea nada."""
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    # Medianoche de un día sin incidencias
    dt = datetime(2026, 9, 23, 0, 0, 5, tzinfo=tz)
    sim_clock = FixedClock(dt.astimezone(UTC))

    from app.db.models import SourceState

    session.add_all([
        SourceState(source="bp", job="initial_load", last_attempt_at=sim_clock.now(), last_success_at=sim_clock.now()),
        SourceState(source="bp", job="regular", last_attempt_at=sim_clock.now(), last_success_at=sim_clock.now()),
    ])
    session.commit()

    worker = SyncWorker(
        engine=session.bind,
        clock=sim_clock,
        app_env="development",
        source_mode="simulated",
        client_factory=lambda src: None,
        curation_loader=lambda: None,
    )

    worker.tick(session)
    session.commit()

    assert session.get(DailySummary, date(2026, 9, 22)) is None


def test_resumen_se_borra_a_los_7_dias(session):
    """RF-154: Cuando un resumen cumpla 7 días, se elimina."""
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    now = datetime(2026, 9, 30, 12, 0, tzinfo=tz).astimezone(UTC)

    # Resumen de hace 8 días (debe borrarse)
    old_day = date(2026, 9, 22)
    # Resumen de hace 3 días (debe conservarse)
    recent_day = date(2026, 9, 27)

    session.add_all([
        DailySummary(day=old_day, content={"total": 1}, created_at=now - timedelta(days=8)),
        DailySummary(day=recent_day, content={"total": 2}, created_at=now - timedelta(days=3)),
    ])
    session.commit()

    deleted = purge_old_entries(session, now)
    session.commit()

    assert deleted >= 1
    assert session.get(DailySummary, old_day) is None
    assert session.get(DailySummary, recent_day) is not None
