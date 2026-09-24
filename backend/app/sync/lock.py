"""Un solo proceso de obtención por base de datos (plan de la spec 003, I-34).

Dos `retake sync` a la vez se pisan: consultan dos veces cada fuente y cada uno anota lo que ve con
su propio reloj. El proceso retiene un bloqueo consultivo de PostgreSQL en una conexión propia
mientras está en marcha:

- Un segundo proceso no lo obtiene y se niega a arrancar.
- Si el proceso termina de cualquier forma, también si se cae, PostgreSQL suelta el bloqueo al
  cerrarse su conexión: nunca queda un bloqueo huérfano.
- El bloqueo es de cada base de datos: las pruebas (`retake_test`) no chocan con el proceso de
  desarrollo (`retake`).
"""

from sqlalchemy import Connection, Engine, text

# Número fijo que identifica el bloqueo de `retake sync` (los bloqueos consultivos se nombran con un entero).
SYNC_LOCK_KEY = 3_003_034


def acquire_sync_lock(engine: Engine) -> Connection | None:
    """Intenta obtener el bloqueo sin esperar.

    Returns:
        La conexión que lo retiene, que hay que pasar a `release_sync_lock`, o None si otro proceso lo tiene.
    """
    connection = engine.connect()
    try:
        acquired = connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": SYNC_LOCK_KEY})
        connection.commit()
    except Exception:
        connection.close()
        raise
    if not acquired:
        connection.close()
        return None
    return connection


def release_sync_lock(connection: Connection) -> None:
    """Suelta el bloqueo y cierra su conexión.

    Hay que soltarlo antes de cerrar: la conexión vuelve al grupo de conexiones sin desconectarse,
    y con ella seguiría retenido.
    """
    try:
        connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SYNC_LOCK_KEY})
        connection.commit()
    finally:
        connection.close()
