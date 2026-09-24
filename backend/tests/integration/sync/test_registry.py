"""T-050 · Pruebas del registro de actualizaciones e incidencias (RF-140 a RF-149)."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.db.models import Incident, IncidentDay, SyncRun
from app.domain.vocabulary import SUMMARY_TIMEZONE
from app.sync.registry import purge_old_entries, record_incident, record_run

T0 = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)
CDMX = ZoneInfo(SUMMARY_TIMEZONE)


def test_registro_de_consulta_crea_sync_run(session):
    """RF-140, RF-141: Una consulta completada registra su fuente, horas, resultado y mensaje recortado."""
    long_msg = "Error: " + ("x" * 600)
    run = record_run(
        session,
        source="bp",
        job="regular",
        started_at=T0,
        finished_at=T0 + timedelta(seconds=5),
        outcome="failure",
        message=long_msg,
    )
    session.commit()

    saved = session.get(SyncRun, run.id)
    assert saved is not None
    assert saved.source == "bp"
    assert saved.job == "regular"
    assert saved.started_at == T0
    assert saved.finished_at == T0 + timedelta(seconds=5)
    assert saved.outcome == "failure"
    assert len(saved.message) <= 500
    assert saved.message.endswith("…")


def test_100_repeticiones_iguales_dejan_una_sola_incidencia_con_contador_100(session):
    """RF-147, RF-148: Criterio 'Hecho cuando': 100 repeticiones iguales dejan una sola incidencia con contador 100."""
    t_start = T0
    for i in range(100):
        t_curr = t_start + timedelta(seconds=i * 10)
        record_incident(
            session,
            source="bp",
            kind="data_rejected",
            subject="player:123:kills",
            reason="valor imposible",
            value="999",
            now=t_curr,
        )
    session.commit()

    incidents = session.scalars(select(Incident)).all()
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.repetitions == 100
    assert inc.first_at == t_start
    assert inc.last_at == t_start + timedelta(seconds=990)
    assert inc.source == "bp"
    assert inc.kind == "data_rejected"
    assert inc.subject == "player:123:kills"
    assert inc.reason == "valor imposible"

    # Se comprueba que IncidentDay también tiene 100 repeticiones para la fecha de CDMX
    day_cdmx = t_start.astimezone(CDMX).date()
    incident_days = session.scalars(select(IncidentDay).where(IncidentDay.incident_id == inc.id)).all()
    assert len(incident_days) == 1
    assert incident_days[0].day == day_cdmx
    assert incident_days[0].repetitions == 100


def test_incidencias_distintas_crean_filas_separadas(session):
    """RF-147: Si difiere la fuente, el tipo, el dato, el valor o el motivo, son incidencias distintas."""
    inc1 = record_incident(session, source="bp", kind="data_rejected", subject="player:1", reason="motivo A", now=T0)
    inc2 = record_incident(session, source="bp", kind="data_rejected", subject="player:2", reason="motivo A", now=T0)
    inc3 = record_incident(session, source="bp", kind="query_failed", subject="regular", reason="timeout", now=T0)
    session.commit()

    count = session.scalar(select(func.count(Incident.id)))
    assert count == 3


def test_nunca_guarda_el_valor_de_un_dato_personal_solo_su_huella(session):
    """RF-60, plan §9: El registro de incidencias nunca guarda el valor de un dato rechazado, solo su huella sha256."""
    personal_value = "John Doe 1999-01-01"
    inc = record_incident(
        session,
        source="bp",
        kind="data_rejected",
        subject="player:42:name",
        reason="formato no reconocido",
        value=personal_value,
        now=T0,
    )
    session.commit()

    saved = session.get(Incident, inc.id)
    assert saved is not None
    assert personal_value not in (saved.subject or "")
    assert personal_value not in (saved.reason or "")
    assert personal_value not in (saved.detail or "")
    # Debe tener una huella hash de 64 caracteres
    assert saved.value_hash is not None
    assert len(saved.value_hash) == 64


def test_repeticiones_en_dias_distintos_actualizan_incident_day_por_dia(session):
    """RF-150 a RF-152: Repeticiones en días naturales distintos de CDMX se distribuyen en incident_day."""
    t_day1 = datetime(2026, 12, 5, 12, 0, tzinfo=UTC)  # 2026-12-05 en CDMX
    t_day2 = datetime(2026, 12, 6, 12, 0, tzinfo=UTC)  # 2026-12-06 en CDMX

    record_incident(session, source="bp", kind="data_rejected", subject="ref:1", reason="err", now=t_day1)
    record_incident(session, source="bp", kind="data_rejected", subject="ref:1", reason="err", now=t_day1)
    record_incident(session, source="bp", kind="data_rejected", subject="ref:1", reason="err", now=t_day2)
    session.commit()

    inc = session.scalar(select(Incident))
    assert inc.repetitions == 3

    days = session.scalars(select(IncidentDay).where(IncidentDay.incident_id == inc.id).order_by(IncidentDay.day)).all()
    assert len(days) == 2
    assert days[0].day == date(2026, 12, 5)
    assert days[0].repetitions == 2
    assert days[1].day == date(2026, 12, 6)
    assert days[1].repetitions == 1


def test_borrado_a_los_7_dias_de_la_ultima_repeticion(session):
    """RF-149, RF-154: Las entradas de más de 7 días se eliminan; las recientes se conservan."""
    old_time = T0 - timedelta(days=8)
    recent_time = T0 - timedelta(days=2)

    # Consulta vieja y reciente
    old_run = record_run(session, "bp", "regular", old_time, old_time, "success")
    recent_run = record_run(session, "bp", "regular", recent_time, recent_time, "success")

    # Incidencia vieja y reciente
    old_inc = record_incident(session, source="bp", kind="query_failed", subject="sub:old", reason="err", now=old_time)
    recent_inc = record_incident(session, source="bp", kind="query_failed", subject="sub:recent", reason="err", now=recent_time)
    session.commit()

    old_run_id = old_run.id
    recent_run_id = recent_run.id
    old_inc_id = old_inc.id
    recent_inc_id = recent_inc.id

    purged = purge_old_entries(session, now=T0)
    session.commit()

    # Old entries are gone
    assert session.get(SyncRun, old_run_id) is None
    assert session.get(Incident, old_inc_id) is None
    assert session.scalars(select(IncidentDay).where(IncidentDay.incident_id == old_inc_id)).all() == []

    # Recent entries remain
    assert session.get(SyncRun, recent_run_id) is not None
    assert session.get(Incident, recent_inc_id) is not None
