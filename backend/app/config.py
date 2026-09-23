"""Configuración del backend leída de variables de entorno y de `backend/.env`.

Las credenciales nunca se escriben en el código (constitución §6.3): se leen de
`DATABASE_URL` y `TEST_DATABASE_URL`. `backend/.env` queda fuera de git; solo se
sube `backend/.env.example`, sin secretos.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta de backend/.env, para que funcione se ejecute desde donde se ejecute.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


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
    """

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str
    test_database_url: str | None = None
    app_env: Literal["development", "test", "production"] = "development"


def load_settings(**overrides) -> Settings:
    """Construye la configuración y traduce los errores a un mensaje claro.

    Args:
        **overrides: Valores que sustituyen a los del entorno (útil en pruebas).

    Raises:
        ConfigError: si falta una variable obligatoria o un valor no es válido.
    """
    try:
        return Settings(**overrides)
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


@lru_cache
def get_settings() -> Settings:
    """Configuración única de la aplicación, leída una sola vez."""
    return load_settings()
