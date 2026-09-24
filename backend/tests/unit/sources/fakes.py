"""Dobles de prueba para los conectores: reloj que avanza al dormir y transporte sin internet."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


class SteppingClock:
    """Reloj falso: `sleep` no espera, solo adelanta la hora (ninguna prueba espera tiempo real)."""

    def __init__(self, start: datetime = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)):
        self.instant = start
        self.slept: list[float] = []

    def now(self) -> datetime:
        return self.instant

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.instant += timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        self.instant += timedelta(seconds=seconds)


@dataclass
class FakeResponse:
    status_code: int
    text: str = ""
    headers: dict = field(default_factory=dict)


class FakeTransport:
    """Responde según la ruta pedida y guarda cada petición (URL, parámetros, cabeceras y hora)."""

    def __init__(self, routes: dict, clock: SteppingClock | None = None):
        self.routes = routes  # url → FakeResponse, lista de FakeResponse (una por llamada) o excepción
        self.clock = clock
        self.calls: list[dict] = []

    def __call__(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout,
                           "at": self.clock.now() if self.clock else None})
        route = self.routes.get(url, FakeResponse(404))
        if isinstance(route, list):
            route = route.pop(0) if len(route) > 1 else route[0]
        if isinstance(route, Exception):
            raise route
        return route
