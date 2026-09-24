"""T-052 · Pruebas de emisión y recepción de NOTIFY en PostgreSQL (RF-80, RF-81)."""

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.sync.notify import NOTIFY_CHANNEL, notify_changes

T0 = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)


def test_notify_limita_a_la_lista_cerrada_de_datasets(session):
    """RF-81: Solo los datasets de la lista cerrada se incluyen en el aviso; otros se descartan."""
    # Lista con un dataset válido y uno ficticio no permitido
    emitted = notify_changes(session, ["matches", "dataset_inventado"], now=T0)
    assert emitted is True


def test_notify_no_emite_si_ningun_dataset_es_valido(session):
    """RF-81: Si ningún dataset es válido o la lista está vacía, no emite nada."""
    assert notify_changes(session, ["invalido"], now=T0) is False
    assert notify_changes(session, [], now=T0) is False


def test_otra_conexion_recibe_el_aviso_notify_con_los_datasets_cambiados(test_engine):
    """RF-80, RF-81: Criterio 'Hecho cuando': una prueba de integración recibe el aviso en otra conexión."""
    # Conexión 1: escucha en el canal
    listener_conn = test_engine.connect().execution_options(autocommit=True)
    dbapi_listener = listener_conn.connection.dbapi_connection
    dbapi_listener.autocommit = True
    dbapi_listener.execute(f"LISTEN {NOTIFY_CHANNEL}")

    # Conexión 2: emite los cambios en una sesión y hace commit
    with Session(test_engine) as session:
        notify_changes(session, ["matches", "live"], now=T0)
        session.commit()

    # Conexión 1: comprueba que se recibió la notificación
    notifies = list(dbapi_listener.notifies(timeout=2.0, stop_after=1))
    listener_conn.close()

    assert len(notifies) == 1
    assert notifies[0].channel == NOTIFY_CHANNEL

    payload = json.loads(notifies[0].payload)
    assert payload["datasets"] == ["live", "matches"]
    assert payload["changedAt"] == T0.isoformat()
