"""Prueba de humo de la API y de la base de datos de pruebas (T-007)."""

from sqlalchemy import text

from app.main import app, engine_or_none
from fastapi.testclient import TestClient


def test_health_con_base_de_datos_disponible(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_sin_base_de_datos_responde_503():
    app.dependency_overrides[engine_or_none] = lambda: None
    try:
        response = TestClient(app).get("/api/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"


def test_las_pruebas_usan_retake_test(clean_db):
    with clean_db.connect() as connection:
        assert connection.execute(text("SELECT current_database()")).scalar_one() == "retake_test"
