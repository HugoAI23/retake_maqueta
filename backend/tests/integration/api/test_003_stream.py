"""T-061 · Canal de eventos del servidor `/api/stream` (spec 003: RF-79 a RF-81, RF-89; plan §3.3).

- Empieza con `retry: 5000` para que el navegador se reconecte solo.
- `change` tras cada aviso `NOTIFY` del proceso de obtención, solo con conjuntos de la lista cerrada.
- `heartbeat` periódico y `freshness` solo para los conjuntos que cambian de estado.
Los datos no viajan por el canal: la página los vuelve a pedir a su ruta.
"""

import asyncio
import json
from datetime import UTC, datetime

from sqlalchemy import text

from app.api.stream import event_stream, pg_notifications
from app.clock import FixedClock

NOW = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)


async def silent():
    """Canal de avisos que nunca avisa."""
    await asyncio.sleep(3600)
    yield ""


async def notifying(*payloads):
    for payload in payloads:
        yield payload
    await asyncio.sleep(3600)


def parse(chunk: str) -> tuple[str | None, dict | None]:
    event = next((line[7:] for line in chunk.splitlines() if line.startswith("event: ")), None)
    data = next((json.loads(line[6:]) for line in chunk.splitlines() if line.startswith("data: ")), None)
    return event, data


async def take(stream, count: int) -> list[str]:
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
        if len(chunks) == count:
            break
    await stream.aclose()
    return chunks


def test_empieza_con_retry_y_avisa_de_cada_cambio():
    payload = json.dumps({"datasets": ["matches", "live", "inventado"], "changedAt": "2026-12-05T20:00:00+00:00"})
    stream = event_stream(notifying(payload, "no es json"), lambda: {}, FixedClock(NOW), heartbeat_seconds=60)
    first, change = asyncio.run(take(stream, 2))
    assert first == "retry: 5000\n\n"
    assert parse(change) == ("change", {"datasets": ["live", "matches"], "changedAt": "2026-12-05T20:00:00+00:00"})


def test_latido_periodico():
    stream = event_stream(silent(), lambda: {}, FixedClock(NOW), heartbeat_seconds=0.05)
    _, beat = asyncio.run(take(stream, 2))
    assert parse(beat) == ("heartbeat", {"now": "2026-12-05T20:00:00+00:00"})


def test_frescura_solo_de_los_conjuntos_que_cambian_de_estado():
    # La primera lectura es la base; después, en cada latido, solo se avisa de lo que cambia.
    states = [{"live": False, "matches": False}, {"live": True, "matches": False}]
    stream = event_stream(silent(), lambda: states.pop(0) if len(states) > 1 else states[0], FixedClock(NOW),
                          heartbeat_seconds=0.05)
    events = [parse(c) for c in asyncio.run(take(stream, 5))[1:]]
    beat = ("heartbeat", {"now": "2026-12-05T20:00:00+00:00"})
    assert events == [beat, ("freshness", {"live": True}), beat, beat]


def test_recibe_el_aviso_real_de_postgresql_tras_una_ingesta(clean_db):
    # RF-80: el proceso de obtención avisa con NOTIFY en el canal `retake_changes` (sync/notify).
    conninfo = clean_db.url.set(drivername="postgresql").render_as_string(hide_password=False)

    async def scenario():
        notifications = pg_notifications(conninfo)
        stream = event_stream(notifications, lambda: {}, FixedClock(NOW), heartbeat_seconds=60)
        assert await anext(stream) == "retry: 5000\n\n"
        pending = asyncio.create_task(anext(stream))
        await asyncio.sleep(0.3)  # el LISTEN ya está en marcha
        with clean_db.begin() as connection:
            connection.execute(text("SELECT pg_notify('retake_changes', :payload)"),
                               {"payload": json.dumps({"datasets": ["matches"], "changedAt": NOW.isoformat()})})
        chunk = await asyncio.wait_for(pending, timeout=5)
        await stream.aclose()
        return chunk

    assert parse(asyncio.run(scenario())) == ("change", {"datasets": ["matches"], "changedAt": NOW.isoformat()})
