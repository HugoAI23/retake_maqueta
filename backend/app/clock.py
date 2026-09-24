"""Reloj inyectable (reglas de ejecución de tasks.md, punto 6).

Las reglas que dependen de "hoy" (edades, cambio de temporada, instante de
observación) reciben un reloj en lugar de leer la hora del sistema, para que las
pruebas puedan fijar el momento exacto.
"""

from datetime import UTC, datetime, timedelta


class SystemClock:
    """Reloj real: la hora actual en UTC."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Reloj de pruebas: devuelve siempre el instante que se le indique."""

    def __init__(self, instant: datetime):
        if instant.tzinfo is None:
            raise ValueError("El instante debe llevar zona horaria (UTC).")
        self.instant = instant

    def now(self) -> datetime:
        return self.instant

    def set(self, instant: datetime) -> None:
        """Mueve el reloj a otro instante."""
        self.instant = instant

    def advance(self, seconds: float | timedelta) -> None:
        """Adelanta el reloj el número de segundos o timedelta indicado."""
        delta = seconds if isinstance(seconds, timedelta) else timedelta(seconds=seconds)
        self.instant += delta



class ScenarioClock:
    """Reloj de la fuente simulada: empieza en la hora de los escenarios y avanza en tiempo real.

    Los escenarios fijan sus partidos en una fecha concreta; con el reloj del sistema, `retake sync`
    en modo simulado no llegaría nunca a esa hora (spec 003, registro I-32 del plan).
    """

    def __init__(self, start: datetime, real=None):
        if start.tzinfo is None:
            raise ValueError("El instante debe llevar zona horaria (UTC).")
        self._real = real or SystemClock()
        self._start = start
        self._real_start = self._real.now()

    def now(self) -> datetime:
        return self._start + (self._real.now() - self._real_start)
