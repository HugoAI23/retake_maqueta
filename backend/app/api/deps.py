"""Dependencias comunes de las rutas: base de datos y reloj."""

from collections.abc import Iterator

from fastapi import Depends, HTTPException
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.clock import SystemClock
from app.db.engine import get_engine


def engine_or_none() -> Engine | None:
    """Devuelve el motor de base de datos, o `None` si no se puede conectar."""
    try:
        return get_engine()
    except Exception:  # noqa: BLE001 — cualquier fallo de conexión cuenta como "no disponible"
        return None


def get_session(engine: Engine | None = Depends(engine_or_none)) -> Iterator[Session]:
    """Sesión de solo lectura por petición; 503 si la base de datos no está disponible."""
    if engine is None:
        raise HTTPException(status_code=503, detail="La base de datos no está disponible.")
    with Session(engine) as session:
        yield session


def get_clock() -> SystemClock:
    """Reloj de la petición: las pruebas lo sustituyen por uno fijo."""
    return SystemClock()
