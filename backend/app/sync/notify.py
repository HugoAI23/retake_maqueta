"""Aviso de cambios a la API mediante LISTEN/NOTIFY de PostgreSQL (plan §2.4, D-6; RF-80, RF-81; T-052)."""

import json
from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.vocabulary import DATASETS

NOTIFY_CHANNEL = "retake_changes"


def notify_changes(
    session: Session,
    datasets: Iterable[str],
    now: datetime | None = None,
    channel: str = NOTIFY_CHANNEL,
) -> bool:
    """Envía un aviso NOTIFY con los conjuntos de datos cambiados (RF-80, RF-81).

    Solo incluye conjuntos de datos que pertenezcan a la lista cerrada DATASETS (RF-81).
    Utiliza parámetros con SQLAlchemy para prevenir inyecciones SQL (plan §9).

    Args:
        session: Sesión de SQLAlchemy en la transacción vigente.
        datasets: Nombres de los conjuntos de datos que sufrieron cambios.
        now: Hora del cambio (UTC).
        channel: Nombre del canal de PostgreSQL.

    Returns:
        True si se emitió el aviso (había al menos un conjunto válido), False en caso contrario.
    """
    valid = sorted({ds for ds in datasets if ds in DATASETS})
    if not valid:
        return False

    instant = now or datetime.now(UTC)
    payload = json.dumps({"datasets": valid, "changedAt": instant.isoformat()})

    session.execute(
        text("SELECT pg_notify(:channel, :payload)"),
        {"channel": channel, "payload": payload},
    )
    return True
