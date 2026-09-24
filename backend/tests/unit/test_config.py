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


# --- Spec 003 (T-009): modo de fuente, proxy de confianza y cookie de sesión ---

URL = "postgresql+psycopg://u@localhost/x"


def test_modo_de_fuente_por_defecto_son_los_datos_de_prueba(monkeypatch):
    # Sin leer backend/.env: `retake source-mode` cambia ahí el modo (T-055).
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.delenv("SOURCE_MODE", raising=False)
    monkeypatch.delenv("TRUSTED_PROXY", raising=False)
    settings = load_settings(database_url=URL, app_env="development")
    assert settings.source_mode == "fixtures"
    assert settings.trusted_proxy is None


def test_modo_de_fuente_no_valido_da_un_error_claro():
    with pytest.raises(ConfigError, match="SOURCE_MODE no es válida"):
        load_settings(database_url=URL, source_mode="internet")


@pytest.mark.parametrize("mode", ["fixtures", "real", "simulated"])
def test_en_desarrollo_se_admiten_los_tres_modos(mode):
    assert load_settings(database_url=URL, app_env="development", source_mode=mode).source_mode == mode


@pytest.mark.parametrize("mode", ["fixtures", "simulated"])
def test_en_produccion_solo_se_admiten_las_fuentes_reales(mode):
    # RF-9: en producción solo hay datos de las fuentes reales.
    with pytest.raises(ConfigError, match="SOURCE_MODE=real"):
        load_settings(database_url=URL, app_env="production", source_mode=mode)


def test_en_produccion_con_fuentes_reales_se_acepta():
    assert load_settings(database_url=URL, app_env="production", source_mode="real").source_mode == "real"


def test_en_las_pruebas_nunca_se_usan_las_fuentes_reales():
    # RF-10: las pruebas automáticas no consultan las fuentes reales.
    with pytest.raises(ConfigError, match="las pruebas no consultan las fuentes reales"):
        load_settings(database_url=URL, app_env="test", source_mode="real")


@pytest.mark.parametrize(("env", "secure"), [("development", False), ("test", False), ("production", True)])
def test_la_cookie_de_sesion_es_segura_solo_en_produccion(env, secure):
    mode = "real" if env == "production" else "fixtures"
    assert load_settings(database_url=URL, app_env=env, source_mode=mode).session_cookie_secure is secure


def test_proxy_de_confianza_opcional():
    settings = load_settings(database_url=URL, trusted_proxy="10.0.0.1")
    assert settings.trusted_proxy == "10.0.0.1"


def test_proxy_de_confianza_vacio_equivale_a_ninguno():
    assert load_settings(database_url=URL, trusted_proxy="").trusted_proxy is None


# --- Spec 003 (T-095, I-26): carpeta de los archivos de la Wiki ---


def test_la_carpeta_de_los_csv_de_la_wiki_por_defecto_es_backend_data_wiki():
    from app.config import BACKEND_DIR

    assert load_settings(database_url=URL).wiki_csv_dir == BACKEND_DIR / "data" / "wiki"


def test_la_carpeta_de_los_csv_de_la_wiki_se_puede_cambiar(tmp_path):
    assert load_settings(database_url=URL, wiki_csv_dir=str(tmp_path)).wiki_csv_dir == tmp_path


def test_los_csv_de_la_wiki_no_se_suben_a_git():
    # Llevan nombres reales y fechas de nacimiento (I-26).
    import subprocess

    from app.config import BACKEND_DIR

    result = subprocess.run(["git", "check-ignore", "-q", str(BACKEND_DIR / "data" / "wiki" / "players_birthday.csv")],
                            cwd=BACKEND_DIR, check=False)
    assert result.returncode == 0
