"""Configuración del backend leída de variables de entorno y de `backend/.env`.

Las credenciales nunca se escriben en el código (constitución §6.3): se leen de
`DATABASE_URL` y `TEST_DATABASE_URL`. `backend/.env` queda fuera de git; solo se
sube `backend/.env.example`, sin secretos.

La spec 003 añade el modo de fuente (`SOURCE_MODE`), el proxy de confianza
(`TRUSTED_PROXY`) y la carpeta de los archivos de la Wiki (`WIKI_CSV_DIR`), y deriva de
`APP_ENV` si la cookie de sesión es segura.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta de backend/.env, para que funcione se ejecute desde donde se ejecute.
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class ConfigError(RuntimeError):
    """Falta una variable obligatoria o tiene un valor no válido."""


class Settings(BaseSettings):
    """Variables de entorno del backend.

    Attributes:
        database_url: Conexión a la base de datos de desarrollo (`retake`).
        test_database_url: Conexión a la base de datos de pruebas (`retake_test`).
            Solo la necesitan las pruebas de integración.
        app_env: Entorno de ejecución. En `production` no se cargan datos
            ficticios ni se publica `/docs` (plan §5).
        source_mode: De dónde salen los datos de la liga (spec 003, RF-9 a RF-11):
            `fixtures` (datos de prueba de la 002), `real` (las fuentes) o
            `simulated` (fuente simulada con escenarios). En producción solo `real`;
            en las pruebas automáticas nunca `real`.
        trusted_proxy: Dirección del proxy cuya cabecera `X-Forwarded-For` se
            acepta para saber el origen de un intento de acceso (plan D-10). Sin
            valor, el origen es siempre la dirección de la conexión.
        wiki_csv_dir: Carpeta con los archivos CSV de la Wiki que prepara Hugo
            (spec 003, C-15 a C-21; plan I-26). Está fuera de git porque llevan
            nombres reales y fechas de nacimiento.
    """

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str
    test_database_url: str | None = None
    app_env: Literal["development", "test", "production"] = "development"
    source_mode: Literal["fixtures", "real", "simulated"] = "fixtures"
    trusted_proxy: str | None = None
    wiki_csv_dir: Path = BACKEND_DIR / "data" / "wiki"

    @field_validator("trusted_proxy", mode="before")
    @classmethod
    def _empty_proxy_is_none(cls, value: object) -> object:
        """`TRUSTED_PROXY=` vacío en `.env` significa "sin proxy de confianza"."""
        return None if isinstance(value, str) and not value.strip() else value

    @property
    def session_cookie_secure(self) -> bool:
        """La cookie de sesión del administrador solo viaja por HTTPS en producción (plan §9)."""
        return self.app_env == "production"


def _check_source_mode(settings: Settings) -> None:
    """Rechaza las combinaciones de entorno y modo de fuente que prohíbe la spec 003.

    Raises:
        ConfigError: en producción con un modo distinto de `real` (RF-9), o en las
            pruebas con `real` (RF-10).
    """
    if settings.app_env == "production" and settings.source_mode != "real":
        raise ConfigError(
            f"En producción solo se admite SOURCE_MODE=real (ahora: {settings.source_mode}): "
            "nunca se usan datos de prueba ni la fuente simulada."
        )
    if settings.app_env == "test" and settings.source_mode == "real":
        raise ConfigError("SOURCE_MODE=real no se admite con APP_ENV=test: las pruebas no consultan las fuentes reales.")


def load_settings(**overrides) -> Settings:
    """Construye la configuración y traduce los errores a un mensaje claro.

    Args:
        **overrides: Valores que sustituyen a los del entorno (útil en pruebas).

    Raises:
        ConfigError: si falta una variable obligatoria, un valor no es válido o el
            modo de fuente no se admite en ese entorno.
    """
    try:
        settings = Settings(**overrides)
    except ValidationError as error:
        problems = []
        for issue in error.errors():
            name = str(issue["loc"][0]).upper()
            if issue["type"] == "missing":
                problems.append(f"falta la variable {name}")
            else:
                problems.append(f"{name} no es válida: {issue['msg']}")
        raise ConfigError(
            "Configuración incompleta: " + "; ".join(problems)
            + f". Revisa {ENV_FILE} (hay un ejemplo en .env.example)."
        ) from None
    _check_source_mode(settings)
    return settings


@lru_cache
def get_settings() -> Settings:
    """Configuración única de la aplicación, leída una sola vez."""
    return load_settings()
