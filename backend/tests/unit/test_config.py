"""Pruebas de la configuración (T-003)."""

import pytest

from app.config import ConfigError, Settings, load_settings


def test_falta_database_url_da_un_error_claro(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Sin leer backend/.env, para simular que no existe.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    with pytest.raises(ConfigError, match="falta la variable DATABASE_URL"):
        load_settings()


def test_app_env_no_valido_da_un_error_claro():
    with pytest.raises(ConfigError, match="APP_ENV no es válida"):
        load_settings(database_url="postgresql+psycopg://u@localhost/x", app_env="staging")


def test_valores_por_defecto():
    settings = load_settings(database_url="postgresql+psycopg://u@localhost/x")
    assert settings.app_env == "development"
