"""Dependencias comunes de las rutas: base de datos y reloj."""

import asyncio
import weakref
from collections.abc import AsyncIterator

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


# Plazas de base de datos por bucle de eventos y motor (plan I-47).
_slots: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


def _db_slots(engine: Engine) -> asyncio.Semaphore:
    """Tantas plazas como conexiones admite el pool del motor (`pool_size` + `max_overflow`)."""
    per_engine = _slots.setdefault(asyncio.get_running_loop(), {})
    if engine not in per_engine:
        pool = engine.pool
        per_engine[engine] = asyncio.Semaphore(pool.size() + max(0, getattr(pool, "_max_overflow", 0)))
    return per_engine[engine]


async def get_session(engine: Engine | None = Depends(engine_or_none)) -> AsyncIterator[Session]:
    """Sesión de solo lectura por petición; 503 si la base de datos no está disponible.

    Plan I-47: nunca hay más peticiones con sesión que conexiones en el pool. Las demás esperan
    su plaza en el bucle de eventos, sin ocupar ningún hilo. Antes, bajo carga, todos los hilos
    esperaban una conexión mientras las peticiones que la tenían esperaban un hilo para validar su
    respuesta y cerrar la sesión: nadie avanzaba hasta que caducaba la espera del pool.
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="La base de datos no está disponible.")
    async with _db_slots(engine):
        with Session(engine) as session:
            yield session


def get_clock() -> SystemClock:
    """Reloj de la petición: las pruebas lo sustituyen por uno fijo."""
    return SystemClock()
