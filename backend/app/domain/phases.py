"""Fases de un partido (RF-31, RF-134; revisión R-1 de la spec)."""

from app.domain.vocabulary import PHASES


def normalize_phase(source_value: object) -> str | None:
    """Traduce la fase publicada por la fuente a una de las cinco fases.

    Admite variantes de escritura ("Winners Bracket", "grand-final"). Cualquier otra
    fase ("play-in", "tiebreaker", "final"…) da `None`: el partido se guarda sin fase.
    """
    if not isinstance(source_value, str):
        return None
    key = source_value.strip().lower().replace(" ", "_").replace("-", "_")
    return key if key in PHASES else None
