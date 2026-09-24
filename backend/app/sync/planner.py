"""Planificador del proceso de obtención (plan de la spec 003, §2.4 y §5; T-049).

Función pura: a partir del estado actual y del instante de tiempo inyectado (reloj),
determina qué consultas e intervenciones internas tocan en cada ciclo (cada 5 s).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.live_priority import LiveMatch, live_cycles
from app.domain.review_windows import needs_review
from app.domain.vocabulary import (
    LIVE_CYCLE,
    MIN_PAUSE,
    PRE_MATCH_WINDOW,
    REST_CYCLE,
    SUMMARY_TIMEZONE,
    SYNC_JOBS,
)


@dataclass(frozen=True)
class ScheduledMatch:
    """Partido programado con su hora de inicio prevista."""

    id: object
    scheduled_at: datetime


@dataclass(frozen=True)
class FinishedMatch:
    """Partido finalizado con la fecha en que se completaron sus estadísticas (o None)."""

    id: object
    stats_complete_at: datetime | None


@dataclass(frozen=True)
class PlannedQuery:
    """Consulta o tarea interna planificada por el planificador.

    `team_id` y `season` identifican una ficha de equipo del "Resto", que el trabajador encola
    tras cada listado con éxito (plan §5, RF-18).
    """

    job: str
    source: str | None = None
    match_id: object | None = None
    day: date | None = None
    team_id: str | None = None
    season: tuple[int, str, str] | None = None

    def __post_init__(self) -> None:
        if self.job not in SYNC_JOBS:
            raise ValueError(f"Tipo de consulta desconocido: {self.job!r}")


@dataclass
class PlannerState:
    """Estado necesario para calcular las consultas a planificar."""

    initial_load_needed: bool = False
    last_regular_at: datetime | None = None
    last_pre_match_at: datetime | None = None
    last_live_list_at: datetime | None = None
    last_live_match_at: dict[object, datetime] = field(default_factory=dict)
    last_finished_match_at: dict[object, datetime] = field(default_factory=dict)
    last_summary_date: date | None = None
    last_cleanup_at: datetime | None = None
    live_matches: Sequence[LiveMatch] = ()
    scheduled_matches: Sequence[ScheduledMatch] = ()
    finished_matches: Sequence[FinishedMatch] = ()
    spotlight_id: str | None = None
    pause: timedelta = field(default_factory=lambda: MIN_PAUSE["bp"])


def plan_queries(state: PlannerState, now: datetime) -> list[PlannedQuery]:
    """Determina las consultas y tareas vencidas según el estado actual y la hora (reloj inyectado).

    Args:
        state: Estado actual de las últimas consultas y partidos en seguimiento.
        now: Instante actual en UTC (con tzinfo).

    Returns:
        Lista ordenada de consultas y tareas a ejecutar en este ciclo.
    """
    # 1. Carga inicial (RF-3, RF-6; plan §5 fila 1):
    # Si la base está vacía o se cambió de modo en desarrollo, va primero y en exclusiva.
    if state.initial_load_needed:
        return [PlannedQuery(job="initial_load", source="bp")]

    planned: list[PlannedQuery] = []

    # 2. Partidos en vivo (RF-16, RF-23 a RF-26, RF-57; plan §5 fila 2):
    # Cada 60 s la lista y la página de cada partido en vivo. Si no caben, el prioritario
    # va cada 60 s y los demás cada 2 min.
    if state.live_matches:
        cycles = live_cycles(state.live_matches, pause=state.pause, spotlight_id=state.spotlight_id)
        for m in state.live_matches:
            last_at = state.last_live_match_at.get(m.id)
            cycle = cycles.get(m.id, LIVE_CYCLE)
            if last_at is None or (now - last_at) >= cycle:
                planned.append(PlannedQuery(job="live", source="bp", match_id=m.id))

        if state.last_live_list_at is None or (now - state.last_live_list_at) >= LIVE_CYCLE:
            planned.append(PlannedQuery(job="live", source="bp", match_id=None))

    # 3. Antes del partido (RF-17; plan §5 fila 3):
    # Cada 60 s mientras algún partido programado esté a 1 h o menos de su hora de inicio,
    # o la haya pasado sin empezar.
    in_pre_match = any(
        now >= m.scheduled_at - PRE_MATCH_WINDOW
        for m in state.scheduled_matches
    )
    if in_pre_match:
        if state.last_pre_match_at is None or (now - state.last_pre_match_at) >= LIVE_CYCLE:
            planned.append(PlannedQuery(job="pre_match", source="bp", match_id=None))

    # 4. Resto (RF-14, RF-18; plan §5 fila 4):
    # Cada hora: calendario, eventos, equipos, identidades, logos, rosters, jugadores, tabla y próxima temporada.
    if state.last_regular_at is None or (now - state.last_regular_at) >= REST_CYCLE:
        planned.append(PlannedQuery(job="regular", source="bp", match_id=None))

    # 5. Partidos terminados (RF-19 a RF-21; plan §5 fila 5):
    # Cada hora cada partido finalizado con estadísticas pendientes o completado hace menos de 7 días.
    for m in state.finished_matches:
        if needs_review(status="finished", stats_complete_at=m.stats_complete_at, now=now):
            last_at = state.last_finished_match_at.get(m.id)
            if last_at is None or (now - last_at) >= REST_CYCLE:
                planned.append(PlannedQuery(job="finished_matches", source="bp", match_id=m.id))

    # 6. Resumen diario (RF-150 a RF-153; plan §5 fila 6):
    # A las 00:00 de America/Mexico_City para el día natural que acaba de terminar.
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    now_local = now.astimezone(tz)
    yesterday = (now_local - timedelta(days=1)).date()

    if state.last_summary_date is None or state.last_summary_date < yesterday:
        start = state.last_summary_date + timedelta(days=1) if state.last_summary_date else yesterday
        earliest_allowed = yesterday - timedelta(days=6)
        if start < earliest_allowed:
            start = earliest_allowed
        curr = start
        while curr <= yesterday:
            planned.append(PlannedQuery(job="daily_summary", source=None, day=curr))
            curr += timedelta(days=1)

    # 7. Limpieza (RF-149, RF-154; plan §5 fila 7):
    # Cada hora: registro, incidencias y resúmenes de más de 7 días.
    if state.last_cleanup_at is None or (now - state.last_cleanup_at) >= REST_CYCLE:
        planned.append(PlannedQuery(job="cleanup", source=None))

    return planned
