"""Cliente educado para consultar las fuentes (plan de la spec 003, §1.2 y §2.2; decisión H-1).

- Se identifica siempre como Retake y nunca se hace pasar por un navegador (RF-37).
- Deja pasar la pausa mínima de su fuente entre dos consultas (RF-39): 2 s.
- Lee una vez las normas para robots de la fuente y no hace una consulta que prohíban (RF-35, RF-42).

La Wiki no se consulta (spec 003, C-18): sus datos llegan por archivos CSV (plan I-26).

El transporte es una función inyectable `(url, params, headers, timeout) → respuesta`: httpx para
BreakingPoint y un transporte simulado en las pruebas (ninguna sale a internet).
"""

from collections.abc import Callable
from typing import Any, Protocol
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from app.domain.vocabulary import MIN_PAUSE
from app.sources.contract import plain_message

VERSION = "0.3"
USER_AGENT = f"Retake/{VERSION} (+https://github.com/HugoAI23/retake_maqueta)"
TIMEOUT_SECONDS = 15

class Response(Protocol):
    status_code: int
    text: str


Transport = Callable[..., Response]


class SourceUnavailable(Exception):
    """La fuente no responde o responde con un error: la consulta ha fallado (RF-43 a RF-45)."""


class Forbidden(Exception):
    """Las normas de la fuente prohíben esta consulta: no se hace (RF-42, RF-143)."""


class PoliteClient:
    """Cliente de una fuente.

    Args:
        source: `bp` o `cdl`; fija la pausa mínima.
        transport: Función que hace la petición HTTP.
        clock: Reloj con `now()` (inyectable, plan §6.2).
        sleep: Función que espera los segundos indicados (en las pruebas solo adelanta el reloj).
        base_url: Origen de la fuente, para leer su `robots.txt`.
    """

    def __init__(self, source: str, transport: Transport, *, clock: Any, sleep: Callable[[float], None], base_url: str):
        self.source = source
        self.pause = MIN_PAUSE[source].total_seconds()
        self._transport = transport
        self._clock = clock
        self._sleep = sleep
        self._base_url = base_url.rstrip("/")
        self._last_request_at = None
        self._robots: RobotFileParser | None = None
        self.robots_unreadable = False
        self.rate_limit_waits = 0

    # --- Normas para robots -------------------------------------------------------------------

    def _load_robots(self) -> None:
        parser = RobotFileParser()
        try:
            response = self._raw_get(f"{self._base_url}/robots.txt")
        except SourceUnavailable:
            response = None
        if response is not None and response.status_code == 200:
            parser.parse(response.text.splitlines())
        elif response is not None and response.status_code == 404:
            parser.parse([])  # no publica normas: todo permitido
        else:
            # Normas ilegibles (p. ej. tapadas por Cloudflare): no hay nada que cumplir, pero se anota.
            self.robots_unreadable = True
            parser.parse([])
        self._robots = parser

    def _check_allowed(self, url: str) -> None:
        if self._robots is None:
            self._load_robots()
        if not self._robots.can_fetch(USER_AGENT, url):
            path = urlsplit(url).path
            raise Forbidden(f"robots.txt de {self._base_url} prohíbe {path} (Disallow)")

    # --- Peticiones ---------------------------------------------------------------------------

    def _wait_turn(self) -> None:
        if self._last_request_at is not None:
            elapsed = (self._clock.now() - self._last_request_at).total_seconds()
            if elapsed < self.pause:
                self._sleep(self.pause - elapsed)

    def _raw_get(self, url: str, params: dict | None = None) -> Response:
        self._wait_turn()
        headers = {"User-Agent": USER_AGENT}
        try:
            response = self._transport(url, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
        except Exception as error:  # noqa: BLE001 — cualquier fallo de red es una fuente no disponible
            raise SourceUnavailable(plain_message(f"{type(error).__name__}: {error}")) from None
        finally:
            self._last_request_at = self._clock.now()
        return response

    def get(self, url: str, params: dict | None = None) -> Response:
        """Consulta una dirección de la fuente.

        Raises:
            Forbidden: si las normas para robots de la fuente lo prohíben.
            SourceUnavailable: si falla la red o la respuesta no es 200.
        """
        self._check_allowed(url)
        response = self._raw_get(url, params)
        if response.status_code != 200:
            raise SourceUnavailable(plain_message(f"HTTP {response.status_code}: {response.text}"))
        return response

def httpx_transport(client: Any) -> Transport:
    """Transporte con un `httpx.Client` (BreakingPoint, H-1)."""

    def get(url: str, params: dict | None = None, headers: dict | None = None, timeout: float | None = None):
        return client.get(url, params=params, headers=headers, timeout=timeout, follow_redirects=True)

    return get


def real_client(source: str) -> PoliteClient:
    """Cliente real de BreakingPoint con httpx (H-1).

    Solo lo usan el proceso de obtención y las comprobaciones manuales: las pruebas usan siempre
    transportes simulados (RF-10). La Wiki no se consulta (spec 003, C-18) y la web de la CDL está
    en reserva, sin conector (I-4).

    Raises:
        ValueError: si se pide otra fuente.
    """
    if source != "bp":
        raise ValueError(f"no hay cliente real para la fuente {source!r}: la Wiki se importa con "
                         "`retake import-wiki-csv` y la web de la CDL está en reserva")
    import time

    import httpx

    from app.clock import SystemClock

    return PoliteClient(source, httpx_transport(httpx.Client()), clock=SystemClock(), sleep=time.sleep,
                        base_url="https://breakingpoint.gg")
