"""Pruebas de la orden `retake source-mode <modo>` (spec 003: RF-11 a RF-13; T-055).

- Se niega fuera de desarrollo (RF-11).
- En desarrollo: borra los datos de la liga guardados (RF-12).
- En desarrollo: deja la base de datos con el modo elegido y programa la carga inicial si aplica (RF-13).
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from app import cli
from app.db.models import Match, Player, Season, SyncJob


def test_source_mode_se_niega_en_produccion(session, tmp_path, capsys):
    """RF-11: En producción o fuera de desarrollo, source-mode se niega a cambiar el modo."""
    with pytest.raises(SystemExit) as exc:
        cli.set_source_mode(session, mode="fixtures", app_env="production", env_file=tmp_path / ".env")
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "solo está permitido en el entorno de desarrollo" in err


def test_source_mode_fixtures_en_desarrollo_carga_fixtures(session, tmp_path):
    """RF-11 a RF-13: Modo 'fixtures' borra la liga, carga los fixtures y actualiza .env."""
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=development\nSOURCE_MODE=real\n", encoding="utf-8")

    cli.set_source_mode(session, mode="fixtures", app_env="development", env_file=env_file)
    session.commit()

    # Comprobar que hay temporadas y jugadores cargados
    seasons = session.scalars(select(Season)).all()
    assert len(seasons) > 0
    players = session.scalars(select(Player)).all()
    assert len(players) > 0

    # Comprobar archivo .env
    assert "SOURCE_MODE=fixtures" in env_file.read_text(encoding="utf-8")


def test_source_mode_simulated_borra_liga_y_programa_carga_inicial(session, tmp_path):
    """RF-12, RF-13: Modo 'simulated' borra datos de la liga y programa carga inicial."""
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=development\n", encoding="utf-8")

    # Primero meter datos de prueba para verificar que luego se borran
    from app.ingest.fixtures import load_fixtures
    load_fixtures(session, app_env="development")
    session.commit()
    assert len(session.scalars(select(Season)).all()) > 0

    # Cambiar a modo simulated
    cli.set_source_mode(session, mode="simulated", app_env="development", env_file=env_file)
    session.commit()

    # Datos de la liga borrados
    assert len(session.scalars(select(Season)).all()) == 0
    assert len(session.scalars(select(Player)).all()) == 0
    assert len(session.scalars(select(Match)).all()) == 0

    # Carga inicial programada en SyncJob
    jobs = session.scalars(select(SyncJob).where(SyncJob.kind == "initial_load")).all()
    assert len(jobs) == 1
    assert jobs[0].done_at is None

    # Archivo .env actualizado
    assert "SOURCE_MODE=simulated" in env_file.read_text(encoding="utf-8")


def test_cambiar_de_modo_borra_el_registro_del_modo_anterior_y_conserva_el_acceso(session, tmp_path):
    """RF-12 (cambio C-27): el registro, las incidencias y los resúmenes son del modo anterior;
    la cuenta de administración, sus sesiones y el bloqueo por intentos fallidos se conservan."""
    from datetime import date

    from app.db.models import AdminSession, AdminUser, DailySummary, Incident, LoginOrigin, SyncRun
    from app.sync.registry import record_incident, record_run

    now = datetime(2026, 12, 5, 19, 0, tzinfo=UTC)  # como las del modo simulado (I-32)
    record_run(session, source="bp", job="regular", started_at=now, finished_at=now, outcome="success")
    record_incident(session, kind="query_failed", source="bp", subject="regular", reason="HTTP 503", now=now)
    session.add(DailySummary(day=date(2026, 12, 4), content={}, created_at=now))
    session.add(AdminUser(username="admin", password_hash="x", created_at=now))
    session.add(AdminSession(token_hash="h" * 64, created_at=now, expires_at=now, last_seen_at=now, origin="127.0.0.1"))
    session.add(LoginOrigin(origin="127.0.0.1", failures=2, updated_at=now))
    session.commit()

    cli.set_source_mode(session, mode="simulated", app_env="development", env_file=tmp_path / ".env")
    session.commit()

    for model in (SyncRun, Incident, DailySummary):
        assert session.scalars(select(model)).all() == [], model.__name__
    for model in (AdminUser, AdminSession, LoginOrigin):
        assert len(session.scalars(select(model)).all()) == 1, model.__name__
