"""Plan I-34 · Un solo `retake sync` por base de datos.

Dos procesos a la vez se pisan: consultan dos veces cada fuente y cada uno anota lo que ve con su
propio reloj (lo vio Hugo al recorrer los escenarios de T-057).
"""

import threading

import pytest

from app.sync.lock import acquire_sync_lock, release_sync_lock
from tests.integration.sync.test_worker import T0, make_worker
from tests.unit.sources.fakes import SteppingClock


def test_un_segundo_proceso_no_obtiene_el_bloqueo(session):
    first = acquire_sync_lock(session.bind)
    assert first is not None
    try:
        assert acquire_sync_lock(session.bind) is None
    finally:
        release_sync_lock(first)
    again = acquire_sync_lock(session.bind)
    assert again is not None
    release_sync_lock(again)


def test_el_trabajador_no_arranca_si_otro_esta_en_marcha(session):
    held = acquire_sync_lock(session.bind)
    try:
        worker = make_worker(session, SteppingClock(T0))
        with pytest.raises(RuntimeError, match="otro `retake sync`"):
            worker.run(stop_event=threading.Event())
    finally:
        release_sync_lock(held)


def test_el_trabajador_suelta_el_bloqueo_al_terminar(session):
    stop = threading.Event()
    stop.set()  # termina sin hacer ningún ciclo
    make_worker(session, SteppingClock(T0)).run(stop_event=stop)
    after = acquire_sync_lock(session.bind)
    assert after is not None
    release_sync_lock(after)


def test_el_trabajador_suelta_el_bloqueo_si_se_detiene_con_un_error(session, monkeypatch):
    worker = make_worker(session, SteppingClock(T0))

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt  # Ctrl+C durante el ciclo

    monkeypatch.setattr(worker, "tick", interrupted)
    with pytest.raises(KeyboardInterrupt):
        worker.run(stop_event=threading.Event())
    after = acquire_sync_lock(session.bind)
    assert after is not None
    release_sync_lock(after)
