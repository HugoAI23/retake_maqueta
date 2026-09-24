"""Número de semana de los partidos de fase `week` (spec 003, T-092; cambio C-13).

Manda la semana que publique una fuente, con la prioridad habitual. Si ninguna la publica, se
calcula entre los partidos de fase `week` del mismo evento (`app.domain.weeks`). Se recalcula
en cada ingesta, porque un partido nuevo de una semana anterior cambia el orden de las demás.
"""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ExternalRef, Match, MatchSchedule, Observation
from app.domain.priority import SourceValue, choose
from app.domain.weeks import week_numbers


def update_weeks(session: Session) -> None:
    """Fija `week` en los partidos de fase `week` y la vacía en los demás."""
    session.flush()
    matches = session.scalars(select(Match).where((Match.phase == "week") | Match.week.is_not(None))).all()
    if not matches:
        return

    latest_schedule: dict = {}
    for match_id, scheduled_at in session.execute(
            select(MatchSchedule.match_id, MatchSchedule.scheduled_at).order_by(MatchSchedule.seq)):
        latest_schedule[match_id] = scheduled_at  # manda la última fecha (RF-87 de la 002)

    published_values: dict = defaultdict(list)
    for entity_id, source, obs in session.execute(
            select(ExternalRef.entity_id, ExternalRef.source, Observation)
            .join(Observation, Observation.ref_id == ExternalRef.id)
            .where(ExternalRef.kind == "match", Observation.field == "week")):
        published_values[entity_id].append(SourceValue(source, obs.value, obs.is_valid, obs.last_seen_at))

    by_event: dict = defaultdict(dict)
    for match in matches:
        if match.phase == "week":
            by_event[match.event_id][match.id] = latest_schedule.get(match.id)
    computed = {match_id: week for dates in by_event.values() for match_id, week in week_numbers(dates).items()}

    for match in matches:
        if match.phase != "week":
            week = None
        else:
            published = choose(published_values.get(match.id, []))
            week = int(published.value) if published is not None else computed[match.id]
        if match.week != week:
            match.week = week
    session.flush()
