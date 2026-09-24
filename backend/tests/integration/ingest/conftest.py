"""Sesión y función de ingesta para las pruebas de integración de la ingesta."""

import pytest
from sqlalchemy.orm import Session

from app.curation.loader import Curation
from app.ingest.pipeline import ingest_records


@pytest.fixture
def session(clean_db):
    with Session(clean_db) as db_session:
        yield db_session


@pytest.fixture
def ingest(session):
    """Ingiere registros con una curación explícita (vacía por defecto) y confirma."""

    def run(records, curation=None, now=None, logo_fetcher=None):
        report = ingest_records(session, records, curation=curation or Curation(), now=now, logo_fetcher=logo_fetcher)
        session.commit()
        return report

    return run
