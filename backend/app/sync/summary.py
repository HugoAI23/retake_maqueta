"""Resumen diario de incidencias a las 00:00 de America/Mexico_City (spec 003: RF-150 a RF-154; T-054).

- Totales y lista de incidencias distintas por fuente (RF-151, RF-152).
- Sin resumen si no hubo incidencias (RF-153).
- Borrado a los 7 días (RF-154, ejecutado en purge_old_entries).
"""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import DailySummary, Incident, IncidentDay, SyncRun
from app.domain.vocabulary import SUMMARY_TIMEZONE


def generate_daily_summary(
    session: Session,
    day: date,
    now: datetime | None = None,
) -> DailySummary | None:
    """Genera el resumen de incidencias de un día natural de Ciudad de México (RF-150 a RF-153).

    Args:
        session: Sesión de SQLAlchemy.
        day: Fecha del día natural en Ciudad de México a resumir.
        now: Hora de creación del resumen (reloj inyectado o UTC actual).

    Returns:
        La instancia de DailySummary creada o actualizada, o None si no hubo incidencias ese día (RF-153).
    """
    instant = now or datetime.now(UTC)

    # 1. Obtener todas las incidencias registradas en este día natural (IncidentDay)
    rows = session.execute(
        select(IncidentDay.repetitions, Incident)
        .join(Incident, IncidentDay.incident_id == Incident.id)
        .where(IncidentDay.day == day)
        .order_by(Incident.id)
    ).all()

    # RF-153: Si no hubo incidencias, no se genera resumen
    if not rows:
        return None

    # Rango temporal en UTC para consultas fallidas en ese día
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    start_dt = datetime(day.year, day.month, day.day, 0, 0, tzinfo=tz).astimezone(UTC)
    end_dt = start_dt + timedelta(days=1)

    # Consultas fallidas por fuente registradas en SyncRun
    run_failures = dict(
        session.execute(
            select(SyncRun.source, func.count(SyncRun.id))
            .where(
                SyncRun.finished_at >= start_dt,
                SyncRun.finished_at < end_dt,
                SyncRun.outcome == "failure",
            )
            .group_by(SyncRun.source)
        ).all()
    )

    by_source: dict[str, dict] = {}
    total_incidents = 0
    total_failed = 0
    total_rejected = 0

    # Agrupar incidencias por fuente
    for reps, inc in rows:
        src = inc.source or "system"
        if src not in by_source:
            by_source[src] = {
                "failed_queries": run_failures.get(src, 0),
                "rejected_data": 0,
                "total_incidents": 0,
                "incidents": [],
            }

        by_source[src]["total_incidents"] += reps
        total_incidents += reps

        if inc.kind == "data_rejected":
            by_source[src]["rejected_data"] += reps
            total_rejected += reps
        elif inc.kind == "query_failed":
            if by_source[src]["failed_queries"] < reps:
                by_source[src]["failed_queries"] = reps

        by_source[src]["incidents"].append({
            "id": inc.id,
            "kind": inc.kind,
            "subject": inc.subject,
            "reason": inc.reason,
            "detail": inc.detail,
            "repetitions": reps,
        })

    for src in by_source:
        total_failed += by_source[src]["failed_queries"]

    content = {
        "day": day.isoformat(),
        "total_incidents": total_incidents,
        "total_failed_queries": total_failed,
        "total_rejected_data": total_rejected,
        "by_source": by_source,
    }

    summary = session.get(DailySummary, day)
    if summary is not None:
        summary.content = content
        summary.created_at = instant
    else:
        summary = DailySummary(day=day, content=content, created_at=instant)
        session.add(summary)

    session.flush()
    return summary
