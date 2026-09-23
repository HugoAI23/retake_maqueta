"""Motor de base de datos compartido por la aplicación."""

from functools import lru_cache

from sqlalchemy import Engine

from app.config import get_settings
from app.db.session import make_engine


@lru_cache
def get_engine() -> Engine:
    """Motor único de la base de datos de `DATABASE_URL`, creado la primera vez que se pide.

    Se crea bajo demanda para que la API pueda arrancar e informar en `/api/health`
    aunque la base de datos no esté disponible todavía.
    """
    return make_engine(get_settings().database_url)
