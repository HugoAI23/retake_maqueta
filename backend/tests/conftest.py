"""Configuración común de pytest.

- `clock`: reloj fijo (22-09-2026 12:00 UTC) que cada prueba puede mover.
- `test_engine`: motor de `retake_test`. Se niega a usar la base de datos de desarrollo.
- `clean_db`: deja `retake_test` vacía y con todas las migraciones aplicadas antes de cada prueba.
- `client`: cliente HTTP de la API conectado a `retake_test`.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import make_url, text

from app.clock import FixedClock
from app.config import load_settings
from app.db.session import make_engine
from app.main import app, engine_or_none

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 9, 22, 12, 0, tzinfo=UTC))


@pytest.fixture(scope="session")
def test_database_url() -> str:
    # Las pruebas fijan su modo de fuente: el de `.env` es el del desarrollo y puede ser `real` (RF-10).
    settings = load_settings(app_env="test", source_mode="fixtures")
    if not settings.test_database_url:
        pytest.fail("Falta TEST_DATABASE_URL en backend/.env: las pruebas de integración la necesitan.")
    test_db = make_url(settings.test_database_url).database
    dev_db = make_url(settings.database_url).database
    if test_db == dev_db:
        pytest.fail(f"TEST_DATABASE_URL apunta a la base de datos de desarrollo ({dev_db}).")
    return settings.test_database_url


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    engine = make_engine(test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def clean_db(test_engine, test_database_url):
    """Borra todo lo que haya en `retake_test` y aplica las migraciones desde cero."""
    test_engine.dispose()
    with test_engine.connect() as connection:
        connection.rollback()
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        connection.commit()
    test_engine.dispose()
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = test_database_url
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
    test_engine.dispose()
    yield test_engine
    test_engine.dispose()




@pytest.fixture
def client(clean_db):
    app.dependency_overrides[engine_or_none] = lambda: clean_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
