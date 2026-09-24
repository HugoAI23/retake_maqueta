"""Cancelación de un partido según la prioridad de fuentes (spec 003: RF-53, RF-146).

Una cancelación solo se aplica si la publica la fuente de mayor prioridad entre las que
publican el partido; si solo la publica una fuente secundaria, el partido se conserva y se
anota la discrepancia como incidencia.
"""

from collections.abc import Mapping, Sequence

from app.domain.priority import SOURCE_PRIORITY

CANCEL = "cancel"
DISCREPANCY = "discrepancy"
KEEP = "keep"


def cancellation_decision(status_by_source: Mapping[str, str], order: Sequence[str] = SOURCE_PRIORITY) -> str:
    """Decide qué hacer con un partido según el estado que publica cada fuente.

    Args:
        status_by_source: Estado de la fuente (`scheduled`, `cancelled`…) de cada fuente
            que publica el partido. Las fuentes que no lo publican no aparecen.

    Returns:
        `CANCEL` si lo cancela la fuente de mayor prioridad que lo publica, `DISCREPANCY`
        si solo lo cancela otra fuente y `KEEP` si ninguna lo cancela.
    """
    publishers = [source for source in order if source in status_by_source]
    if not publishers:
        return KEEP
    if status_by_source[publishers[0]] == "cancelled":
        return CANCEL
    if any(status == "cancelled" for status in status_by_source.values()):
        return DISCREPANCY
    return KEEP
