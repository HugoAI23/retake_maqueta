"""Estado de un partido (RF-35, RF-62, RF-63, RF-81 a RF-83; plan §3.4 y D-6)."""

from dataclasses import dataclass

# Rango de cada estado de Retake: un partido nunca baja de rango (RF-62).
STATUS_RANK = {"scheduled": 1, "live": 2, "finished": 3}

# Estado de la fuente → estado de Retake. `None` = el partido se deja de guardar (RF-83).
SOURCE_STATUS_MAP = {
    "scheduled": "scheduled",
    "postponed": "scheduled",
    "live": "live",
    "finished": "finished",
    "forfeit": "finished",
    "cancelled": None,
}


@dataclass(frozen=True)
class StatusChange:
    """Resultado de aplicar un estado de la fuente.

    Attributes:
        status: Estado de Retake que queda, o `None` si el partido se cancela.
        cancelled: El partido deja de guardarse (RF-83).
        postponed: La fuente lo aplaza; hay que añadir la nueva fecha (RF-81, RF-87).
        forfeit: Se decidió por forfeit: ganador y marcador de la fuente, sin mapas (RF-82).
        started: El partido ha empezado, lo que puede fijar el inicio de su temporada (RF-3).
    """

    status: str | None
    cancelled: bool = False
    postponed: bool = False
    forfeit: bool = False
    started: bool = False


def apply_source_status(current: str | None, source_status: str) -> StatusChange:
    """Aplica el estado que publica la fuente al estado guardado.

    Args:
        current: Estado guardado en Retake, o `None` si el partido es nuevo.
        source_status: `scheduled`, `postponed`, `live`, `finished`, `forfeit` o `cancelled`.

    Raises:
        ValueError: si el estado de la fuente no es ninguno de los anteriores.
    """
    if source_status not in SOURCE_STATUS_MAP:
        raise ValueError(f"Estado de fuente desconocido: {source_status!r}")

    target = SOURCE_STATUS_MAP[source_status]
    if target is None:
        return StatusChange(status=None, cancelled=True)

    # Si la fuente publica un estado anterior al guardado, se conserva el guardado (RF-63).
    status = target
    if current is not None and STATUS_RANK[target] < STATUS_RANK[current]:
        status = current

    forfeit = source_status == "forfeit"
    return StatusChange(
        status=status,
        postponed=source_status == "postponed",
        forfeit=forfeit,
        # Llegar a en vivo o más allá cuenta como empezado; un forfeit no se juega.
        started=STATUS_RANK[status] >= STATUS_RANK["live"] and not forfeit,
    )
