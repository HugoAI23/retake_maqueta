"""T-049 · Pruebas del planificador de consultas (RF-3, RF-6, RF-14, RF-16 a RF-21, RF-23 a RF-29, RF-150; plan §5)."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.clock import FixedClock
from app.domain.live_priority import LiveMatch
from app.domain.vocabulary import SUMMARY_TIMEZONE
from app.sync.planner import (
    FinishedMatch,
    PlannedQuery,
    PlannerState,
    ScheduledMatch,
    plan_queries,
)

T0 = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)
CDMX = ZoneInfo(SUMMARY_TIMEZONE)


def test_carga_inicial_planifica_solo_initial_load_en_primer_lugar():
    """RF-3, RF-6: Si la base está vacía o se necesita carga inicial, se planifica initial_load antes que nada."""
    state = PlannerState(
        initial_load_needed=True,
        live_matches=[LiveMatch("m1", T0)],
        last_regular_at=None,
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    assert len(planned) == 1
    assert planned[0] == PlannedQuery(job="initial_load", source="bp")


def test_partido_en_vivo_se_consulta_cada_60_segundos_con_su_lista():
    """RF-16: Un partido en vivo y el listado en vivo se consultan al menos cada 60 s."""
    state = PlannerState(
        initial_load_needed=False,
        live_matches=[LiveMatch("m1", T0)],
        last_live_match_at={"m1": T0 - timedelta(seconds=60)},
        last_live_list_at=T0 - timedelta(seconds=60),
        last_regular_at=T0,
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    jobs = [(p.job, p.match_id) for p in planned]
    assert ("live", "m1") in jobs
    assert ("live", None) in jobs


def test_partido_en_vivo_no_se_consulta_si_no_ha_pasado_su_ciclo():
    """RF-16: Si no ha pasado el ciclo de 60 s, no se planifica de nuevo."""
    state = PlannerState(
        initial_load_needed=False,
        live_matches=[LiveMatch("m1", T0)],
        last_live_match_at={"m1": T0 - timedelta(seconds=30)},
        last_live_list_at=T0 - timedelta(seconds=30),
        last_regular_at=T0,
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    live_queries = [p for p in planned if p.job == "live"]
    assert len(live_queries) == 0


def test_varios_partidos_en_vivo_con_prioridad_si_no_caben():
    """RF-23 a RF-26: Con pausa que impide consultar todos en 60 s, el prioritario va cada 60 s y el secundario cada 2 min."""
    m_temprano = LiveMatch("temprano", T0)
    m_tarde = LiveMatch("tarde", T0 + timedelta(minutes=30))
    state = PlannerState(
        initial_load_needed=False,
        live_matches=[m_temprano, m_tarde],
        pause=timedelta(seconds=25),
        last_live_match_at={
            "temprano": T0 - timedelta(seconds=60),
            "tarde": T0 - timedelta(seconds=60),
        },
        last_live_list_at=T0 - timedelta(seconds=60),
        last_regular_at=T0,
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    jobs = [(p.job, p.match_id) for p in planned]
    assert ("live", "temprano") in jobs
    assert ("live", "tarde") not in jobs
    assert ("live", None) in jobs

    clock.set(T0 + timedelta(seconds=60))
    planned_later = plan_queries(state, clock.now())
    jobs_later = [(p.job, p.match_id) for p in planned_later]
    assert ("live", "tarde") in jobs_later


def test_antes_del_partido_se_consulta_la_lista_a_menos_de_1_hora():
    """RF-17: Si un partido programado está a 1 hora o menos de su hora de inicio (o la pasó sin empezar), se consulta cada 60s."""
    scheduled = ScheduledMatch("prog_1", T0 + timedelta(minutes=45))
    state = PlannerState(
        initial_load_needed=False,
        scheduled_matches=[scheduled],
        last_pre_match_at=T0 - timedelta(seconds=60),
        last_regular_at=T0,
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    pre_matches = [p for p in planned if p.job == "pre_match"]
    assert len(pre_matches) == 1
    assert pre_matches[0] == PlannedQuery(job="pre_match", source="bp", match_id=None)


def test_antes_del_partido_tambien_si_paso_su_hora_sin_empezar():
    """RF-17: Si pasó su hora de inicio y sigue programado, se sigue consultando cada 60 s."""
    scheduled = ScheduledMatch("prog_retrasado", T0 - timedelta(minutes=10))
    state = PlannerState(
        initial_load_needed=False,
        scheduled_matches=[scheduled],
        last_pre_match_at=T0 - timedelta(seconds=60),
        last_regular_at=T0,
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    pre_matches = [p for p in planned if p.job == "pre_match"]
    assert len(pre_matches) == 1


def test_antes_del_partido_no_se_consulta_si_falta_mas_de_1_hora():
    """RF-17: Si falta más de 1 hora para el partido programado, no se planifica pre_match."""
    scheduled = ScheduledMatch("prog_lejos", T0 + timedelta(hours=2))
    state = PlannerState(
        initial_load_needed=False,
        scheduled_matches=[scheduled],
        last_pre_match_at=None,
        last_regular_at=T0,
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    pre_matches = [p for p in planned if p.job == "pre_match"]
    assert len(pre_matches) == 0


def test_resto_se_consulta_cada_hora():
    """RF-14, RF-18: El resto de datos (calendario, tabla, equipos, próxima temporada) se consulta cada hora."""
    state = PlannerState(
        initial_load_needed=False,
        last_regular_at=T0 - timedelta(hours=1),
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    regular = [p for p in planned if p.job == "regular"]
    assert len(regular) == 1
    assert regular[0] == PlannedQuery(job="regular", source="bp", match_id=None)

    state.last_regular_at = T0 - timedelta(minutes=30)
    planned_soon = plan_queries(state, clock.now())
    assert not any(p.job == "regular" for p in planned_soon)


def finished_state(finished, attempts=None):
    return PlannerState(
        initial_load_needed=False,
        finished_matches=[finished],
        last_finished_match_at=attempts or {},
        last_regular_at=T0,
        last_cleanup_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )


def finished_queries(state):
    return [p for p in plan_queries(state, FixedClock(T0).now()) if p.job == "finished_matches"]


def test_un_partido_recien_finalizado_se_consulta_una_vez():
    """RF-19 (C-25): al finalizar, o al registrarse ya finalizado, se consulta su página."""
    assert finished_queries(finished_state(FinishedMatch("nuevo", first_checked_at=None, reviews_done=0))) == [
        PlannedQuery(job="finished_matches", source="bp", match_id="nuevo")]


def test_despues_se_revisa_una_vez_al_dia_durante_tres_dias():
    """RF-20 (C-25): a las 24, 48 y 72 horas de la primera consulta."""
    due = FinishedMatch("m", first_checked_at=T0 - timedelta(hours=48), reviews_done=1)
    not_yet = FinishedMatch("m", first_checked_at=T0 - timedelta(hours=30), reviews_done=1)
    assert len(finished_queries(finished_state(due))) == 1
    assert finished_queries(finished_state(not_yet)) == []


def test_tras_las_tres_revisiones_no_se_consulta_mas():
    """RF-21: fuera de los plazos de RF-19 y RF-20, solo a petición del administrador."""
    done = FinishedMatch("m", first_checked_at=T0 - timedelta(days=10), reviews_done=3)
    assert finished_queries(finished_state(done)) == []


def test_una_consulta_de_partido_finalizado_que_fallo_se_repite_a_la_hora():
    """RF-45: una consulta fallida se repite en el siguiente ciclo, no en cada vuelta de 5 s."""
    pending = FinishedMatch("m", first_checked_at=None, reviews_done=0)
    assert finished_queries(finished_state(pending, {"m": T0 - timedelta(minutes=30)})) == []
    assert len(finished_queries(finished_state(pending, {"m": T0 - timedelta(hours=1)}))) == 1


def test_resumen_diario_se_planifica_a_las_00_00_de_ciudad_de_mexico():
    """RF-150: A las 00:00 de Ciudad de México se genera el resumen del día natural que acaba de terminar."""
    midnight_cdmx = datetime(2026, 12, 6, 0, 0, 0, tzinfo=CDMX).astimezone(UTC)
    yesterday_date = date(2026, 12, 5)

    state = PlannerState(
        initial_load_needed=False,
        last_summary_date=date(2026, 12, 4),
        last_regular_at=midnight_cdmx,
        last_cleanup_at=midnight_cdmx,
    )
    clock = FixedClock(midnight_cdmx)
    planned = plan_queries(state, clock.now())

    summary_queries = [p for p in planned if p.job == "daily_summary"]
    assert len(summary_queries) == 1
    assert summary_queries[0] == PlannedQuery(job="daily_summary", source=None, day=yesterday_date)


def test_resumen_diario_no_se_repite_si_ya_se_genero_el_del_dia_anterior():
    """RF-150: Si el resumen del día anterior ya fue generado, no se vuelve a pedir en ciclos posteriores."""
    midnight_cdmx = datetime(2026, 12, 6, 0, 5, 0, tzinfo=CDMX).astimezone(UTC)
    yesterday_date = date(2026, 12, 5)

    state = PlannerState(
        initial_load_needed=False,
        last_summary_date=yesterday_date,
        last_regular_at=midnight_cdmx,
        last_cleanup_at=midnight_cdmx,
    )
    clock = FixedClock(midnight_cdmx)
    planned = plan_queries(state, clock.now())

    assert not any(p.job == "daily_summary" for p in planned)


def test_limpieza_cada_hora():
    """RF-149, RF-154: La tarea de limpieza se planifica cada hora."""
    state = PlannerState(
        initial_load_needed=False,
        last_cleanup_at=T0 - timedelta(hours=1),
        last_regular_at=T0,
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    cleanups = [p for p in planned if p.job == "cleanup"]
    assert len(cleanups) == 1
    assert cleanups[0] == PlannedQuery(job="cleanup", source=None)


def test_recuperacion_tras_parada_ejecuta_consultas_vencidas_en_el_primer_ciclo():
    """RF-27 a RF-29: Tras una parada prolongada (ej: 4 horas), las consultas vencidas se emiten de inmediato sin valores intermedios."""
    stoppage_time = T0 - timedelta(hours=4)
    live = LiveMatch("m_live", T0)
    scheduled = ScheduledMatch("m_sched", T0 + timedelta(minutes=15))
    finished = FinishedMatch("m_fin", first_checked_at=None, reviews_done=0)

    state = PlannerState(
        initial_load_needed=False,
        last_regular_at=stoppage_time,
        last_cleanup_at=stoppage_time,
        last_pre_match_at=stoppage_time,
        last_live_list_at=stoppage_time,
        last_live_match_at={"m_live": stoppage_time},
        last_finished_match_at={"m_fin": stoppage_time},
        last_summary_date=(T0.astimezone(CDMX) - timedelta(days=1)).date(),
        live_matches=[live],
        scheduled_matches=[scheduled],
        finished_matches=[finished],
    )
    clock = FixedClock(T0)
    planned = plan_queries(state, clock.now())

    jobs = {(p.job, p.match_id) for p in planned}
    assert ("live", "m_live") in jobs
    assert ("live", None) in jobs
    assert ("pre_match", None) in jobs
    assert ("regular", None) in jobs
    assert ("finished_matches", "m_fin") in jobs
    assert ("cleanup", None) in jobs
    assert len([p for p in planned if p.job == "regular"]) == 1
    assert len([p for p in planned if p.job == "cleanup"]) == 1
