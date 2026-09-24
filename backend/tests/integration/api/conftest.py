"""Cliente de la API con todos los datos de prueba cargados una sola vez por módulo."""

from datetime import UTC, datetime

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_clock
from app.clock import FixedClock
from app.config import load_settings
from app.db.session import make_engine
from app.ingest.fixtures import load_fixtures
from app.main import app, engine_or_none
from tests.conftest import BACKEND_DIR

TODAY = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def api():
    url = load_settings(app_env="test", source_mode="fixtures").test_database_url
    engine = make_engine(url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes.update(database_url=url, configure_logger=False)
    command.upgrade(config, "head")
    with Session(engine) as session:
        load_fixtures(session, app_env="test")
        session.commit()
    app.dependency_overrides[engine_or_none] = lambda: engine
    app.dependency_overrides[get_clock] = lambda: FixedClock(TODAY)
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def ids(api):
    """Identificadores internos a partir de referencias externas, para las rutas de detalle."""
    from app.ingest.store import entity_for

    engine = app.dependency_overrides[engine_or_none]()

    def lookup(kind, ref):
        with Session(engine) as session:
            return str(entity_for(session, kind, ref))

    return lookup
