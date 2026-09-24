"""Resultado de una consulta a una fuente (plan de la spec 003, §3.1).

Es lo que un conector entrega al proceso de obtención: los registros de fuente, las
referencias vistas (para las desapariciones) y los datos que no ha podido entender.
"""

from dataclasses import dataclass, field, replace

from app.domain.vocabulary import RUN_OUTCOMES

# Longitud máxima de un mensaje de una fuente (RF-120).
MESSAGE_LIMIT = 500


def plain_message(text: object) -> str | None:
    """Mensaje recibido de una fuente como texto plano de una línea y 500 caracteres como máximo.

    No se interpreta nada (RF-119): el HTML queda como texto literal. Los espacios y saltos
    de línea seguidos se reducen a uno; si sobra texto, se corta y se termina en "…" (RF-120).
    """
    if text is None:
        return None
    flat = " ".join(str(text).split())
    if len(flat) <= MESSAGE_LIMIT:
        return flat
    return flat[: MESSAGE_LIMIT - 1] + "…"


@dataclass(frozen=True)
class Rejection:
    """Dato que el conector no ha podido entender (RF-47, RF-48, RF-142).

    `value_excerpt` es un fragmento del valor publicado, recortado; el registro de
    incidencias solo guardará su huella (plan §9).
    """

    ref: str
    field: str
    reason: str
    value_excerpt: str | None = None


@dataclass(frozen=True)
class ConsultaResult:
    """Lo que devuelve una consulta.

    Attributes:
        source: `bp`, `wiki` o `cdl`.
        job: Tipo de consulta del planificador (plan §5).
        outcome: `success`, `partial`, `failure` o `forbidden`.
        records: Registros de fuente, en el orden en que deben ingerirse.
        seen: Referencias (`fuente:id`) que incluía la respuesta (RF-50 a RF-52).
        rejected: Datos no entendidos.
        message: Motivo de un fallo, como texto plano recortado.
        item_count: Elementos de la respuesta, para reconocer una respuesta vacía (RF-46).
    """

    source: str
    job: str
    outcome: str
    records: list[dict] = field(default_factory=list)
    seen: list[str] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)
    message: str | None = None
    item_count: int | None = None

    def __post_init__(self) -> None:
        if self.outcome not in RUN_OUTCOMES:
            raise ValueError(f"Resultado de consulta desconocido: {self.outcome!r}")
        object.__setattr__(self, "message", plain_message(self.message))

    def with_rejections_outcome(self) -> "ConsultaResult":
        """Un éxito con datos rechazados pasa a ser parcial (RF-105)."""
        if self.outcome == "success" and self.rejected:
            return replace(self, outcome="partial")
        return self


class UnreadableResponse(Exception):
    """La respuesta de la fuente no tiene el formato esperado: la consulta falla (RF-45 a RF-47)."""
