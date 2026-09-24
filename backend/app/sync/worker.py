"""Trabajador del proceso de obtención (spec 003: RF-9 a RF-11, RF-16, RF-44, RF-100, RF-107, RF-136; T-053).

Ejecuta el bucle de obtención periódica (cada 5 s, plan §2.4 y §5):
- Una cola por fuente (RF-44) para que la pausa de una no frene a las demás. Dentro de cada cola
  van primero las peticiones del administrador y lo en vivo, y al final la revisión de partidos
  terminados, para que el en vivo cumpla su ciclo de 60 s (RF-16).
- Tras cada listado con éxito, encola las fichas de cada equipo del "Resto" (tabla, rosters y
  jugadores; RF-18).
- Recuerda cuándo consultó cada partido en vivo y cada partido terminado, para respetar sus
  ciclos (60 s y 1 h; RF-16, RF-19, RF-20), y cuándo limpió el registro (cada hora).
- Recoge y atiende peticiones del administrador (`sync_request`), con una sola en curso por fuente (RF-107).
- No arranca en modo `fixtures` ni, en producción, con fuentes simuladas o datos ficticios (RF-9 a RF-11).
- Termina lo empezado aunque la sesión que lo pidió caduque (RF-136).
- Solo corre un proceso por base de datos: un segundo `retake sync` se niega a arrancar (I-34).
"""

import itertools
import time
import uuid
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clock import ScenarioClock, SystemClock
from app.config import get_settings
from app.curation.loader import Curation, load_curation
from app.db.engine import get_engine
from app.db.models import (
    DailySummary,
    Event,
    ExternalRef,
    Identity,
    Incident,
    Match,
    MatchSchedule,
    Player,
    SourceState,
    SyncJob,
    SyncRequest,
    SyncRun,
)
from app.domain.live_priority import LiveMatch
from app.domain.vocabulary import SOURCES
from app.sources.contract import ConsultaResult
from app.sources.http import real_client
from app.sync.lock import acquire_sync_lock, release_sync_lock
from app.sync.planner import FinishedMatch, PlannedQuery, PlannerState, ScheduledMatch, plan_queries
from app.sync.registry import purge_old_entries, record_incident, record_run
from app.sync.runner import LISTING_JOBS, consult, execute_consultation

# Orden dentro de la cola de una fuente: primero lo que tiene el ciclo más corto (plan §5, RF-16).
REQUEST_RANK = 0
JOB_RANK = {"live": 1, "pre_match": 2, "initial_load": 3, "regular": 4, "finished_matches": 6}
TEAM_PAGE_RANK = 5


def verify_source_mode(source_mode: str) -> None:
    """En modo `fixtures` los datos son los de prueba de la 002: no se consulta ninguna fuente (RF-9 a RF-11).

    Raises:
        RuntimeError: en modo `fixtures`.
    """
    if source_mode == "fixtures":
        raise RuntimeError(
            "En modo fixtures los datos de la liga son los de prueba y no se consulta ninguna fuente. "
            "Para obtener datos, cambia de modo con `uv run retake source-mode real` o `simulated` (RF-9 a RF-11)."
        )


def verify_production_safety(session: Session, app_env: str, source_mode: str) -> None:
    """Comprueba que no se utilicen fuentes simuladas ni datos ficticios en producción (RF-9).

    Raises:
        RuntimeError: si en producción el modo no es 'real' o si la base contiene datos ficticios.
    """
    if app_env != "production":
        return
    if source_mode != "real":
        raise RuntimeError(
            f"En producción solo se admite SOURCE_MODE=real (ahora: {source_mode}): "
            "nunca se usan datos de prueba ni la fuente simulada (RF-9)."
        )
    fictitious = (
        session.scalar(select(ExternalRef.id).where(ExternalRef.fictional.is_(True)).limit(1))
        or session.scalar(select(Identity.id).where(Identity.short_name.like("%[FICTICIO]%")).limit(1))
        or session.scalar(select(Event.id).where(Event.name.like("%[FICTICIO]%")).limit(1))
        or session.scalar(select(Player.id).where(Player.current_gamertag.like("%[FICTICIO]%")).limit(1))
    )
    if fictitious is not None:
        raise RuntimeError(
            "La base de datos contiene datos ficticios; en producción solo se permiten fuentes reales (RF-9)."
        )


def _real_logo_fetcher() -> Callable[[str], bytes]:
    """Descarga de logos con el cliente educado (RF-65 a RF-71; plan I-20)."""
    import httpx

    from app.logos import download_logo
    from app.sources.http import httpx_transport

    transport = httpx_transport(httpx.Client())
    clock = SystemClock()
    return lambda url: download_logo(url, transport, clock=clock, sleep=time.sleep)


class SyncWorker:
    """Trabajador que orquesta las colas de sincronización periódica y peticiones administrativas."""

    def __init__(
        self,
        engine=None,
        client_factory: Callable[[str], Any] | None = None,
        clock=None,
        curation_loader: Callable[[], Curation] | None = None,
        app_env: str | None = None,
        source_mode: str | None = None,
        loop_interval: float = 5.0,
        consult_fn: Callable[[PlannedQuery, Any, datetime], ConsultaResult] | None = None,
        logo_fetcher: Callable[[str], bytes] | None = None,
    ):
        self.engine = engine or get_engine()
        self.curation_loader = curation_loader or load_curation
        settings = get_settings() if (app_env is None or source_mode is None) else None
        self.app_env = app_env or (settings.app_env if settings else "development")
        self.source_mode = source_mode or (settings.source_mode if settings else "fixtures")
        if clock is None and self.source_mode == "simulated":
            from app.sources.simulated import SCENARIO_START

            clock = ScenarioClock(SCENARIO_START)  # los escenarios viven en su propia fecha (I-32)
        self.clock = clock or SystemClock()
        self.loop_interval = loop_interval
        self.consult_fn = consult_fn or consult
        self.logo_fetcher = logo_fetcher

        if client_factory is not None:
            self.client_factory = client_factory
        elif self.source_mode == "simulated":
            import os

            from app.sources import bp
            from app.sources.http import PoliteClient
            from app.sources.simulated import simulated_transport

            scenario = os.getenv("SIMULATED_SCENARIO", "partido_en_vivo")
            transport = simulated_transport(scenario, self.clock, app_env=self.app_env)
            self.client_factory = lambda src: PoliteClient(
                src,
                transport=transport,
                clock=self.clock,
                sleep=lambda s: None,
                base_url=bp.BASE_URL,
            )
        else:
            self.client_factory = real_client
            if self.logo_fetcher is None and self.source_mode == "real":
                self.logo_fetcher = _real_logo_fetcher()

        # Una cola por fuente (RF-44); cada elemento es (orden, llegada, consulta, petición).
        self.queues: dict[str, list[tuple[int, int, PlannedQuery, uuid.UUID | None]]] = {
            s: [] for s in SOURCES if s != "wiki"
        }
        self._arrivals = itertools.count()
        # Peticiones administrativas en curso por fuente (RF-107)
        self.running_requests: dict[str, uuid.UUID] = {}
        # Cuándo se consultó cada partido y cuándo se limpió el registro (plan §5)
        self.last_live_match_at: dict[str, datetime] = {}
        self.last_finished_match_at: dict[str, datetime] = {}
        self.last_cleanup_at: datetime | None = None
        # Último día procesado para el resumen diario (RF-150 a RF-153)
        self.last_evaluated_summary_date: date | None = None

    # --- Colas ----------------------------------------------------------------------------------

    def enqueue(self, query: PlannedQuery, request_id: uuid.UUID | None = None) -> None:
        """Añade una consulta a la cola de su fuente, salvo que ya esté esperando."""
        queue = self.queues.get(query.source)
        if queue is None or any(item[2] == query for item in queue):
            return
        if request_id is not None:
            rank = REQUEST_RANK
        elif query.team_id is not None:
            rank = TEAM_PAGE_RANK
        else:
            rank = JOB_RANK.get(query.job, TEAM_PAGE_RANK)
        queue.append((rank, next(self._arrivals), query, request_id))

    def _pop(self, source: str) -> tuple[PlannedQuery, uuid.UUID | None]:
        queue = self.queues[source]
        item = min(queue, key=lambda entry: (entry[0], entry[1]))
        queue.remove(item)
        return item[2], item[3]

    # --- Estado para el planificador ------------------------------------------------------------

    @staticmethod
    def _bp_ids(session: Session, match_ids: list) -> dict:
        """Identificador en BreakingPoint de cada partido: es el que necesita su página (`/match/{id}`)."""
        if not match_ids:
            return {}
        rows = session.execute(select(ExternalRef.entity_id, ExternalRef.source_id).where(
            ExternalRef.kind == "match", ExternalRef.source == "bp", ExternalRef.entity_id.in_(match_ids)))
        return dict(rows.all())

    @staticmethod
    def _latest_schedule(session: Session, match_id) -> datetime | None:
        """Manda la última fecha y hora de inicio publicada (RF-87 de la 002)."""
        return session.scalar(select(MatchSchedule.scheduled_at).where(MatchSchedule.match_id == match_id)
                              .order_by(MatchSchedule.seq.desc()).limit(1))

    def build_planner_state(self, session: Session, now: datetime) -> PlannerState:
        """Extrae de la base de datos la información requerida por el planificador."""
        s_init = session.get(SourceState, ("bp", "initial_load"))
        s_reg = session.get(SourceState, ("bp", "regular"))
        has_initial_job = session.scalar(
            select(SyncJob.id).where(SyncJob.kind == "initial_load", SyncJob.done_at.is_(None)).limit(1)
        )
        initial_load_needed = has_initial_job is not None or (
            (s_init is None or s_init.last_success_at is None) and (s_reg is None or s_reg.last_success_at is None)
        )
        s_prem = session.get(SourceState, ("bp", "pre_match"))
        s_live = session.get(SourceState, ("bp", "live"))

        # Solo los partidos que publica BreakingPoint: se consultan por su página (plan §5).
        live_rows = session.scalars(select(Match).where(Match.status == "live")).all()
        sched_rows = session.scalars(select(Match).where(Match.status == "scheduled")).all()
        fin_rows = session.scalars(select(Match).where(Match.status == "finished")).all()
        bp_ids = self._bp_ids(session, [m.id for m in (*live_rows, *fin_rows)])

        live_matches = [LiveMatch(bp_ids[m.id], self._latest_schedule(session, m.id) or m.went_live_at or now)
                        for m in live_rows if m.id in bp_ids]
        scheduled = [(m, self._latest_schedule(session, m.id)) for m in sched_rows]
        scheduled_matches = [ScheduledMatch(str(m.id), at) for m, at in scheduled if at is not None]
        finished_matches = [FinishedMatch(bp_ids[m.id], m.stats_complete_at) for m in fin_rows if m.id in bp_ids]

        last_db_summary = session.scalar(select(func.max(DailySummary.day)))
        summary_dates = [d for d in (self.last_evaluated_summary_date, last_db_summary) if d is not None]

        return PlannerState(
            initial_load_needed=initial_load_needed,
            # La carga inicial es también un listado completo: el "Resto" cuenta desde la última.
            last_regular_at=max((s.last_attempt_at for s in (s_init, s_reg) if s and s.last_attempt_at), default=None),
            last_pre_match_at=s_prem.last_attempt_at if s_prem else None,
            last_live_list_at=s_live.last_attempt_at if s_live else None,
            last_live_match_at=dict(self.last_live_match_at),
            last_finished_match_at=dict(self.last_finished_match_at),
            last_summary_date=max(summary_dates) if summary_dates else None,
            last_cleanup_at=self.last_cleanup_at,
            live_matches=live_matches,
            scheduled_matches=scheduled_matches,
            finished_matches=finished_matches,
        )

    # --- Peticiones del administrador -----------------------------------------------------------

    def process_sync_requests(self, session: Session, now: datetime) -> None:
        """Atiende peticiones sync_request pendientes según RF-100 a RF-111."""
        pending = session.scalars(
            select(SyncRequest).where(SyncRequest.status == "pending").order_by(SyncRequest.requested_at)
        ).all()

        for req in pending:
            # C-19: La Wiki no se actualiza por sincronización
            if req.source == "wiki":
                req.status = "done"
                req.result = "forbidden"
                req.finished_at = now
                req.message = "La Wiki no se actualiza por sincronización; sus datos entran por import-wiki-csv (C-19)."
                continue

            # RF-107: Solo una petición en curso por fuente a la vez
            if req.source in self.running_requests:
                continue

            if req.source not in self.queues:
                req.status = "done"
                req.result = "failure"
                req.finished_at = now
                req.message = f"Fuente no soportada: {req.source}"
                continue

            # RF-100: sin esperar al siguiente ciclo, el listado completo va el primero de su cola;
            # sus fichas de equipo se encolan después, como en el "Resto".
            req.status = "running"
            req.started_at = now
            self.running_requests[req.source] = req.id
            self.enqueue(PlannedQuery(job="regular", source=req.source), request_id=req.id)

    # --- Ciclo ------------------------------------------------------------------------------------

    def _execute(self, s: Session, source: str, query: PlannedQuery, req_id, curation: Curation, now: datetime) -> None:
        """Ejecuta una consulta de la cola y anota su resultado (RF-43 a RF-47, RF-140 a RF-146)."""
        if query.match_id is not None:
            timers = self.last_live_match_at if query.job == "live" else self.last_finished_match_at
            timers[query.match_id] = now
        follow_up = query.team_id is not None
        incidents_before = s.scalar(select(func.count(Incident.id)).where(Incident.source == source)) or 0
        last_run_before = s.scalar(select(func.max(SyncRun.id))) or 0

        try:
            result = self.consult_fn(query, self.client_factory(source), now)
            execute_consultation(s, result, curation=curation, now=now, request_id=req_id,
                                 logo_fetcher=self.logo_fetcher, follow_up=follow_up)
        except Exception as error:  # noqa: BLE001 — un fallo inesperado no para el proceso (RF-44)
            s.rollback()
            message = f"{type(error).__name__}: {error}"
            if not follow_up:
                state = s.get(SourceState, (source, query.job)) or SourceState(source=source, job=query.job)
                s.add(state)
                state.last_attempt_at = now
            record_run(s, source=source, job=query.job, started_at=now, finished_at=now, outcome="failure",
                       message=message, request_id=req_id)
            record_incident(s, kind="query_failed", source=source, subject=query.job, reason=message, now=now)
            s.commit()
            result = None

        run = s.scalar(select(SyncRun).where(SyncRun.id > last_run_before, SyncRun.source == source)
                       .order_by(SyncRun.id.desc()).limit(1))
        outcome = run.outcome if run is not None else "failure"
        print(f"[retake sync] {source} {query.job}"
              f"{' ' + str(query.match_id or query.team_id) if (query.match_id or query.team_id) else ''}: {outcome}")

        # Tras un listado con éxito, las fichas de cada equipo del "Resto" (RF-18).
        if (result is not None and not follow_up and query.job in LISTING_JOBS
                and outcome in ("success", "partial") and result.teams and result.season):
            for team_id in result.teams:
                self.enqueue(PlannedQuery(job=query.job, source=source, team_id=team_id, season=result.season))

        # Si venía de una petición administrativa, finalizarla (RF-104 a RF-106, RF-136)
        if req_id is not None:
            req = s.get(SyncRequest, req_id)
            if req is not None:
                incidents_after = s.scalar(select(func.count(Incident.id)).where(Incident.source == source)) or 0
                req.status = "done"
                req.result = outcome
                req.finished_at = now
                req.incident_count = max(0, incidents_after - incidents_before)
            self.running_requests.pop(source, None)

    def tick(self, session: Session | None = None, now: datetime | None = None) -> None:
        """Ejecuta un ciclo del planificador y avanza las colas de fuentes."""
        instant = now or self.clock.now()

        def _do_tick(s: Session):
            verify_production_safety(s, self.app_env, self.source_mode)

            # 1. Planificar consultas periódicas y tareas internas
            state = self.build_planner_state(s, instant)
            for q in plan_queries(state, instant):
                if q.source:
                    self.enqueue(q)
                elif q.job == "cleanup":
                    purge_old_entries(s, instant)
                    self.last_cleanup_at = instant
                elif q.job == "daily_summary" and q.day:
                    from app.sync.summary import generate_daily_summary

                    generate_daily_summary(s, day=q.day, now=instant)
                    self.last_evaluated_summary_date = q.day
            s.commit()

            # 2. Recoger peticiones administrativas (RF-100 a RF-108)
            self.process_sync_requests(s, instant)
            s.commit()

            # 3. Procesar un elemento por fuente activa (RF-44)
            curation = self.curation_loader()
            for source in self.queues:
                if self.queues[source]:
                    query, req_id = self._pop(source)
                    self._execute(s, source, query, req_id, curation, instant)
            s.commit()

        if session is not None:
            _do_tick(session)
        else:
            with Session(self.engine) as s:
                _do_tick(s)

    def run(self, stop_event=None) -> None:
        """Bucle continuo del trabajador que ejecuta tick() cada loop_interval segundos.

        Raises:
            RuntimeError: en modo `fixtures`, en producción con fuentes simuladas o datos ficticios,
                o si ya hay otro `retake sync` en marcha contra la misma base de datos (I-34).
        """
        verify_source_mode(self.source_mode)
        with Session(self.engine) as s:
            verify_production_safety(s, self.app_env, self.source_mode)

        lock = acquire_sync_lock(self.engine)
        if lock is None:
            raise RuntimeError(
                "Ya hay otro `retake sync` en marcha contra esta base de datos. Dos a la vez se pisan: "
                "detén el otro (Ctrl+C en su terminal; `pgrep -fl \"retake sync\"` lo localiza) y vuelve a intentarlo."
            )
        try:
            print(f"[retake sync] Iniciando sincronización en modo '{self.source_mode}' (intervalo: {self.loop_interval}s)...")
            while stop_event is None or not stop_event.is_set():
                try:
                    self.tick()
                except Exception as err:  # noqa: BLE001 — el proceso sigue en el siguiente ciclo
                    print(f"[retake sync] error en el ciclo: {type(err).__name__}: {err}")
                time.sleep(self.loop_interval)
        finally:
            release_sync_lock(lock)
