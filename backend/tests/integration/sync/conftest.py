"""Fixtures para las pruebas de integración de app.sync."""

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def session(clean_db):
    with Session(clean_db) as db_session:
        yield db_session
