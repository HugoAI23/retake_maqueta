"""Canal de eventos del servidor `/api/stream` (spec 003: RF-79 a RF-81, RF-89; plan §3.3, H-6, D-6).

- `retry: 5000` al empezar: el navegador se reconecta solo a los 5 s si se corta.
- `change` con los conjuntos de datos cambiados, tras cada aviso `NOTIFY` del proceso de
  obtención (`sync/notify`). Solo nombres de la lista cerrada `DATASETS`.
- `heartbeat` cada 15 s; sin él en 45 s, el frontend da el canal por cortado.
- `freshness` solo para los conjuntos que cambian de estado (sin actualizar ↔ al día).

Los datos no viajan por el canal: la página los vuelve a pedir a su ruta normal, así que las
reglas de la 002 y el filtro de temporada se aplican siempre en un único sitio.
"""

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable

import anyio
from starlette.responses import StreamingResponse

from app.domain.vocabulary import DATASETS
from app.sync.notify import NOTIFY_CHANNEL

HEARTBEAT_SECONDS = 15
RETRY_MS = 5000


def sse(event: str, data: dict) -> str:
    """Un evento en el formato de eventos del servidor."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _change(payload: str) -> dict | None:
    """Aviso del proceso de obtención → datos del evento `change`, o `None` si no se entiende."""
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return None
    datasets = sorted({d for d in data.get("datasets") or [] if d in DATASETS}) if isinstance(data, dict) else []
    return {"datasets": datasets, "changedAt": data.get("changedAt")} if datasets else None


async def pg_notifications(conninfo: str) -> AsyncIterator[str]:
    """Avisos del canal `retake_changes` de PostgreSQL (`LISTEN`, plan D-6)."""
    import psycopg

    connection = await psycopg.AsyncConnection.connect(conninfo, autocommit=True)
    try:
        await connection.execute(f"LISTEN {NOTIFY_CHANNEL}")  # nombre fijo, no viene de fuera
        async for notification in connection.notifies():
            yield notification.payload
    finally:
        await connection.close()


async def event_stream(
    notifications: AsyncIterator[str],
    freshness_fn: Callable[[], dict[str, bool]],
    clock,
    heartbeat_seconds: float = HEARTBEAT_SECONDS,
    is_disconnected: Callable[[], Awaitable[bool]] | None = None,
) -> AsyncIterator[str]:
    """Eventos del canal para una página abierta.

    Args:
        notifications: Avisos del proceso de obtención (texto JSON de `sync/notify`).
        freshness_fn: Estado "sin actualizar" de cada conjunto (`{conjunto: bool}`).
        clock: Reloj para la hora del latido.
        heartbeat_seconds: Cada cuánto se envía el latido.
        is_disconnected: Indica si la página ya se ha ido (para cerrar la conexión).
    """
    yield f"retry: {RETRY_MS}\n\n"
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str] = asyncio.Queue()

    async def pump() -> None:
        async for payload in notifications:
            await queue.put(payload)

    # Plan I-47: la escucha arranca dentro del bloque que la cierra, para que ningún fallo o
    # cancelación (por ejemplo, en la primera consulta de frescura) la deje abierta.
    listener = asyncio.create_task(pump())
    try:
        previous = await asyncio.to_thread(freshness_fn)
        next_beat = loop.time() + heartbeat_seconds
        while True:
            if is_disconnected is not None and await is_disconnected():
                return
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=max(0.0, next_beat - loop.time()))
            except TimeoutError:
                next_beat = loop.time() + heartbeat_seconds
                yield sse("heartbeat", {"now": clock.now().isoformat()})
            else:
                change = _change(payload)
                if change is None:
                    continue
                yield sse("change", change)
            current = await asyncio.to_thread(freshness_fn)
            changed = {dataset: stale for dataset, stale in current.items() if previous.get(dataset) != stale}
            previous = current
            if changed:
                yield sse("freshness", changed)
    finally:
        listener.cancel()
        try:
            await listener
        except (asyncio.CancelledError, Exception):  # noqa: BLE001 — la conexión ya se cierra
            pass
        await notifications.aclose()


class EventStreamResponse(StreamingResponse):
    """Respuesta del canal que siempre cierra su generador (plan I-47).

    Si la página se va mientras se envía un evento, Starlette cancela el envío y el generador se
    queda suspendido en su `yield`, sin llegar a su `finally`: la conexión `LISTEN` con PostgreSQL
    seguía abierta para siempre. Aquí se cierra al terminar la respuesta, protegido de la
    cancelación para que el cierre de la conexión llegue a completarse.
    """

    async def __call__(self, scope, receive, send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            with anyio.CancelScope(shield=True):
                await self.body_iterator.aclose()
