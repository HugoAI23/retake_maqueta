"""Conexión con PostgreSQL (plan de la spec 002, §1 y P-5).

El proyecto usa PostgreSQL 18. Al conectar se comprueba la versión del servidor
y se rechaza cualquier versión anterior, porque en el equipo de desarrollo hay
instaladas dos versiones (14 y 18) que usan el mismo puerto (plan §8).
"""

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection

# PostgreSQL expone su versión como número: 18.4 → 180004.
MIN_SERVER_VERSION_NUM = 180000


class UnsupportedDatabaseError(RuntimeError):
    """El servidor de PostgreSQL es anterior a la versión 18."""


def ensure_supported_version(version_num: int) -> None:
    """Rechaza un servidor anterior a PostgreSQL 18.

    Args:
        version_num: Valor de `server_version_num` (p. ej. 140020 para la 14.20).

    Raises:
        UnsupportedDatabaseError: si la versión es anterior a la 18.
    """
    if version_num < MIN_SERVER_VERSION_NUM:
        major = version_num // 10000
        raise UnsupportedDatabaseError(
            f"PostgreSQL {major} no es compatible: Retake necesita PostgreSQL 18. "
            "Detén la versión antigua (brew services stop postgresql@14) "
            "y arranca la 18 (brew services start postgresql@18)."
        )


def check_server_version(connection: Connection) -> int:
    """Lee la versión del servidor de una conexión abierta y la valida.

    Returns:
        El número de versión del servidor.
    """
    version_num = int(connection.execute(text("SHOW server_version_num")).scalar_one())
    ensure_supported_version(version_num)
    return version_num


def make_engine(database_url: str) -> Engine:
    """Crea el motor de SQLAlchemy y valida la versión en la primera conexión."""
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        check_server_version(connection)
    return engine
