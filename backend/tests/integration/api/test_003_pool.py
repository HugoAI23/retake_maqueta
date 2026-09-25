"""Plan I-47 · La API no se bloquea cuando se llenan a la vez el pool de conexiones y los hilos.

En las pruebas del navegador, las sesiones que ya habían terminado esperaban un hilo libre para
cerrarse y devolver su conexión, mientras todos los hilos estaban ocupados por peticiones que
esperaban esa conexión: nadie avanzaba hasta que caducaba la espera del pool (30 s) y los canales
de eventos se acumulaban hasta llenar PostgreSQL.
"""

import asyncio

import anyio.to_thread
import httpx
from sqlalchemy import create_engine

from app.main import app, engine_or_none


def test_con_el_pool_y_los_hilos_llenos_todas_las_peticiones_terminan(api):
    original = app.dependency_overrides[engine_or_none]
    small = create_engine(original().url, pool_size=1, max_overflow=0, pool_timeout=2)
    app.dependency_overrides[engine_or_none] = lambda: small

    async def scenario():
        # Menos hilos que peticiones, y una sola conexión: el caso límite, en pequeño.
        anyio.to_thread.current_default_thread_limiter().total_tokens = 2
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            responses = await asyncio.gather(*(client.get("/api/season/current") for _ in range(4)))
        return [response.status_code for response in responses]

    try:
        assert asyncio.run(scenario()) == [200, 200, 200, 200]
        assert small.pool.checkedout() == 0
    finally:
        app.dependency_overrides[engine_or_none] = original
        small.dispose()
