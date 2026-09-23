"""T-050, T-056 y T-057 · Casos de la API que necesitan una base de datos propia."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.curation.loader import Curation
from app.ingest.pipeline import ingest_records
from app.main import create_app


def rec(kind, sid, hours=0, **fields):
    return {"kind": kind, "source": "bp", "source_id": sid, "observed_at": f"2026-01-10T{12 + hours:02d}:00:00Z", **fields}


def ingest(engine, records):
    with Session(engine) as session:
        report = ingest_records(session, records, curation=Curation())
        session.commit()
    assert report.rejected == []


def test_sin_temporada_empezada_la_temporada_actual_da_404(client):
    assert client.get("/api/season/current").status_code == 404


def test_la_temporada_actual_cambia_al_empezar_la_siguiente(client, clean_db):
    ingest(clean_db, [rec("season", "s26", year=2026), rec("event", "e26", season_year=2026, name="E26"),
                      rec("match", "m26", event_ref="bp:e26", best_of=5, status="live")])
    assert client.get("/api/season/current").json()["year"] == 2026
    ingest(clean_db, [rec("season", "s27", hours=1, year=2027), rec("event", "e27", hours=1, season_year=2027, name="E27"),
                      rec("match", "m27", hours=1, event_ref="bp:e27", best_of=5, status="live")])
    assert client.get("/api/season/current").json()["year"] == 2027


def test_un_campeonato_no_terminado_no_aparece(client, clean_db):
    ingest(clean_db, [rec("championship", "c2026", year=2026, completed=True),
                      rec("championship", "c2027", year=2027, completed=False)])
    assert [c["year"] for c in client.get("/api/championships").json()] == [2026]


def test_en_produccion_no_hay_docs():
    production = TestClient(create_app(app_env="production"))
    assert production.get("/docs").status_code == 404
    assert production.get("/openapi.json").status_code == 404
