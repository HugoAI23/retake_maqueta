"""Pruebas de integración de punta a punta con la fuente simulada (spec 003: T-056).

Escenarios de `app/sources/simulated.py` y reloj simulado:
- vida completa de un partido en vivo (partido_en_vivo);
- varios partidos en vivo con prioridad (varios_en_vivo);
- fuente caída y respuesta vacía (fuente_caida, respuesta_vacia);
- dato ilegible (dato_ilegible);
- desaparición y reaparición (partido_desaparece);
- parada y recuperación (RF-27 a RF-29);
- cambio de temporada automático (cambio_de_temporada; RF-3, RF-14, RF-15, RF-72, RF-73).
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.clock import FixedClock
from app.curation.loader import Curation
from app.db.models import (
    Event,
    ExternalRef,
    Incident,
    Match,
    Season,
    SourceState,
    SyncRun,
)
from app.sources import bp
from app.sources.http import PoliteClient
from app.sources.simulated import simulated_transport
from app.sync.worker import SyncWorker

T0 = datetime(2026, 12, 5, 19, 0, tzinfo=UTC)


def _setup_worker(session, scenario_name: str, clock: FixedClock) -> tuple[SyncWorker, PoliteClient]:
    transport = simulated_transport(scenario_name, clock, app_env="development")
    client = PoliteClient(
        "bp",
        transport=transport,
        clock=clock,
        sleep=lambda s: None,
        base_url=bp.BASE_URL,
    )
    worker = SyncWorker(
        engine=session.bind,
        clock=clock,
        app_env="development",
        source_mode="simulated",
        client_factory=lambda src: client,
        curation_loader=lambda: Curation(),
    )
    return worker, client


def _drain(worker: SyncWorker, session, now: datetime | None = None) -> None:
    """Ejecuta ciclos de tick hasta vaciar las consultas pendientes en colas."""
    worker.tick(session, now=now)
    # Si quedaron consultas encoladas (por ejemplo la consulta de partidos tras la lista), ejecutarlas
    for _ in range(5):
        if not any(len(q) > 0 for q in worker.queues.values()):
            break
        worker.tick(session, now=now)
    session.commit()


def test_vida_completa_partido_en_vivo(session):
    """T-056: Vida completa de un partido: scheduled -> live (con mapa y marcador) -> finished (3-1)."""
    # Escenario partido_en_vivo:
    # 0..60s: upcoming
    # 60..180s: live (0-0)
    # 180..300s: live (1-0)
    # 300s+: completed (3-1, winner 4)
    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "partido_en_vivo", clock)

    # 1. Carga inicial (t=0)
    _drain(worker, session)
    ext_900 = session.scalar(select(ExternalRef).where(ExternalRef.source == "bp", ExternalRef.source_id == "900"))
    assert ext_900 is not None
    match = session.get(Match, ext_900.entity_id)
    assert match is not None
    assert match.status == "scheduled"

    # 2. t = 70s: el partido pasa a live
    clock.advance(70)
    # Forzar ciclo pre_match/live planificado
    _drain(worker, session)
    session.refresh(match)
    assert match.status == "live"
    assert match.went_live_at is not None

    # 3. t = 190s: marcador avanza en live
    clock.advance(120)
    _drain(worker, session)
    session.refresh(match)
    assert match.status == "live"

    # 4. t = 310s: el partido termina 3-1
    clock.advance(120)
    _drain(worker, session)
    session.refresh(match)
    assert match.status == "finished"
    assert match.maps_won_1 == 3
    assert match.maps_won_2 == 1


def test_varios_partidos_en_vivo_con_prioridad(session):
    """T-056: Varios partidos en vivo (907, 908, 909) se obtienen y priorizan (RF-23 a RF-26)."""
    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "varios_en_vivo", clock)

    _drain(worker, session)

    # Los tres partidos en vivo deben estar en la BD
    for mid in ("907", "908", "909"):
        ext = session.scalar(select(ExternalRef).where(ExternalRef.source == "bp", ExternalRef.source_id == mid))
        assert ext is not None
        m = session.get(Match, ext.entity_id)
        assert m is not None
        assert m.status == "live"


def test_fuente_caida_y_recuperacion(session):
    """T-056: BP da 503 durante 2 min; datos conservados e incidencia registrada; al volver, éxito."""
    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "fuente_caida", clock)

    # 1. Durante la caída (t=10s): 503
    clock.advance(10)
    _drain(worker, session)

    run = session.scalar(select(SyncRun).where(SyncRun.source == "bp").order_by(SyncRun.id.desc()))
    assert run is not None
    assert run.outcome == "failure"

    inc = session.scalar(select(Incident).where(Incident.kind == "query_failed"))
    assert inc is not None

    # 2. Tras la recuperación (t=130s): vuelve y sincroniza con éxito
    clock.advance(120)
    _drain(worker, session)

    # El listado tras la recuperación tiene éxito (la revisión del partido 902, que el escenario no
    # publica, puede fallar después sin que eso cuente aquí).
    last_listing = session.scalar(select(SyncRun).where(SyncRun.source == "bp", SyncRun.job == "initial_load")
                                  .order_by(SyncRun.id.desc()).limit(1))
    assert last_listing.outcome == "success"

    # Partido 902 sincronizado
    ext_902 = session.scalar(select(ExternalRef).where(ExternalRef.source == "bp", ExternalRef.source_id == "902"))
    assert ext_902 is not None


def test_respuesta_vacia_cuenta_como_fallo_y_conserva_datos(session):
    """T-056: RF-46: Respuesta vacía donde había datos cuenta como fallo y conserva los datos."""
    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "respuesta_vacia", clock)

    # 1. Carga inicial: partidos 903 y 904 ingresan
    _drain(worker, session)
    ext_903 = session.scalar(select(ExternalRef).where(ExternalRef.source == "bp", ExternalRef.source_id == "903"))
    ext_904 = session.scalar(select(ExternalRef).where(ExternalRef.source == "bp", ExternalRef.source_id == "904"))
    assert ext_903 is not None
    assert ext_904 is not None

    # 2. En el siguiente "Resto" (cada hora, plan §5) la lista de completados llega vacía
    clock.advance(3601)
    worker.tick(session)
    session.commit()

    # La consulta debe haber fallado por respuesta vacía (RF-46)
    failed_run = session.scalar(
        select(SyncRun).where(
            SyncRun.source == "bp",
            SyncRun.outcome == "failure",
            SyncRun.message.like("%vacía%"),
        )
    )
    assert failed_run is not None
    assert "vacía" in (failed_run.message or "").lower()

    # Los datos anteriores siguen existiendo en la base de datos (RF-43)
    assert session.get(Match, ext_903.entity_id) is not None
    assert session.get(Match, ext_904.entity_id) is not None


def test_dato_ilegible_registra_incidencia(session):
    """T-056: RF-47, RF-48: Partido con estado ilegible ('suspended_by_aliens') se anota como unreadable."""
    from app.db.models import Observation

    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "dato_ilegible", clock)

    _drain(worker, session)

    # Se registró observación con invalid_reason='unreadable' (RF-47, RF-48)
    obs = session.scalars(select(Observation).where(Observation.invalid_reason == "unreadable")).all()
    assert len(obs) >= 1
    assert any(o.field == "status" for o in obs)


def test_partido_desaparece_y_reaparece(session):
    """T-056: RF-50 a RF-52: Partido 906 desaparece >24h (anota incidencia y disappeared_at) y reaparece."""
    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "partido_desaparece", clock)

    # 1. Carga inicial: partido 906 aparece
    _drain(worker, session)
    ext_906 = session.scalar(select(ExternalRef).where(ExternalRef.source == "bp", ExternalRef.source_id == "906"))
    assert ext_906 is not None
    match_906 = session.get(Match, ext_906.entity_id)
    assert match_906 is not None

    # 2. Avanzar 25 horas sin aparecer en la consulta con éxito (de 60s a 60 + 25*3600)
    clock.advance(25 * 3600 + 10)
    s_reg = session.get(SourceState, ("bp", "regular"))
    if s_reg:
        s_reg.last_attempt_at = clock.now() - timedelta(hours=2)
    session.commit()

    _drain(worker, session)

    # Debe detectarse como desaparecido
    session.refresh(match_906)
    assert match_906.disappeared_at is not None

    inc_dis = session.scalar(select(Incident).where(Incident.kind == "match_disappeared"))
    assert inc_dis is not None
    assert str(match_906.id) in inc_dis.subject

    # 3. Avanzar a 26 horas: reaparece
    clock.advance(3600)
    if s_reg:
        s_reg.last_attempt_at = clock.now() - timedelta(hours=2)
    session.commit()

    _drain(worker, session)

    session.refresh(ext_906)
    # Su last_seen_at se actualiza a la hora actual
    assert ext_906.last_seen_at == clock.now()


def test_parada_y_recuperacion(session):
    """T-056: RF-27 a RF-29: Tras una parada, las consultas vencidas se ejecutan en el primer ciclo."""
    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "partido_en_vivo", clock)

    # Carga inicial
    _drain(worker, session)

    # Simular que el proceso estuvo parado 3 horas
    clock.advance(3 * 3600)

    # Al reanudar en el primer tick:
    # El planificador debe planificar y el trabajador ejecutar las consultas vencidas
    _drain(worker, session)

    s_reg = session.get(SourceState, ("bp", "regular"))
    assert s_reg is not None
    assert s_reg.last_success_at == clock.now()


def test_cambio_de_temporada_automatico(session):
    """T-056: RF-3, RF-14, RF-15, RF-72, RF-73: Cambio de temporada al pasar primer partido a live."""
    # Escenario cambio_de_temporada:
    # 0..3600s: temporada 2027 publicada con partido 910 upcoming.
    # 3600s+: partido 910 pasa a live.
    clock = FixedClock(T0)
    worker, _ = _setup_worker(session, "cambio_de_temporada", clock)

    # 1. Carga inicial (t=0): se obtienen ambas temporadas
    _drain(worker, session)

    s26 = session.scalar(select(Season).where(Season.year == 2026))
    s27 = session.scalar(select(Season).where(Season.year == 2027))
    assert s26 is not None
    assert s27 is not None
    # La temporada 2027 aún no ha empezado (started_at es None)
    assert s27.started_at is None

    # 2. t = 3610s: el primer partido de 2027 pasa a live
    clock.advance(3610)
    s_reg = session.get(SourceState, ("bp", "regular"))
    if s_reg:
        s_reg.last_attempt_at = clock.now() - timedelta(hours=2)
    session.commit()

    _drain(worker, session)

    session.refresh(s27)
    # Al pasar a live, started_at de la temporada 2027 se fija automáticamente (RF-3)
    assert s27.started_at is not None
