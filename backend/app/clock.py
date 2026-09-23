"""Reloj inyectable (reglas de ejecución de tasks.md, punto 6).

Las reglas que dependen de "hoy" (edades, cambio de temporada, instante de
observación) reciben un reloj en lugar de leer la hora del sistema, para que las
pruebas puedan fijar el momento exacto.
"""

from datetime import UTC, datetime


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
