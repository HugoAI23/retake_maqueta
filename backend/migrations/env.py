"""Entorno de Alembic de Retake.

La conexión sale de `DATABASE_URL` (app.config), nunca de alembic.ini. Las pruebas
pueden apuntar a otra base de datos pasando la URL en `config.attributes["database_url"]`.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import get_settings
from app.db.base import Base
import app.db.models  # noqa: F401 — registra todas las tablas en Base.metadata
from app.db.session import check_server_version

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    """URL de la base de datos: la que pase quien invoca a Alembic o la de DATABASE_URL."""
    return config.attributes.get("database_url") or get_settings().database_url


def run_migrations_offline() -> None:
    """Genera el SQL de las migraciones sin conectar a la base de datos."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica las migraciones sobre la base de datos, tras comprobar que es PostgreSQL 18."""
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        check_server_version(connection)
        # La consulta de versión abre una transacción implícita (SQLAlchemy 2). Si no se
        # cierra, Alembic la toma por una transacción externa, no hace commit y las
        # migraciones se deshacen al cerrar la conexión.
        connection.commit()
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
