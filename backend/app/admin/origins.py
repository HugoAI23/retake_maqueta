"""Bloqueo por origen tras 5 intentos fallidos seguidos (spec 003: RF-127 a RF-133; plan D-10).

El origen es la dirección del cliente. Detrás de un proxy, solo se usa la que añade él a
`X-Forwarded-For` si es el proxy de confianza configurado (`TRUSTED_PROXY`); si no, esa cabecera
se ignora, porque cualquiera podría escribirla.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import LoginOrigin
from app.domain.vocabulary import LOGIN_BLOCK, LOGIN_MAX_FAILURES
from app.sync.registry import record_incident


def client_origin(peer: str | None, forwarded_for: str | None, trusted_proxy: str | None) -> str:
    """Origen de una petición: la IP del cliente, o la que añade el proxy de confianza."""
    if trusted_proxy and peer == trusted_proxy and forwarded_for:
        return forwarded_for.split(",")[-1].strip()[:64]  # la última la añade el propio proxy
    return (peer or "desconocido")[:64]


def _row(session: Session, origin: str, now: datetime) -> LoginOrigin:
    row = session.get(LoginOrigin, origin)
    if row is None:
        row = LoginOrigin(origin=origin, failures=0, updated_at=now)
        session.add(row)
    if row.blocked_until is not None and row.blocked_until <= now:
        row.failures, row.blocked_until, row.updated_at = 0, None, now  # RF-132
    return row


def is_blocked(session: Session, origin: str, now: datetime) -> bool:
    """Si el origen está bloqueado ahora (RF-129); al acabar el bloqueo, el contador vuelve a cero."""
    return _row(session, origin, now).blocked_until is not None


def record_failure(session: Session, origin: str, now: datetime) -> bool:
    """Suma un intento fallido; al quinto seguido bloquea 15 min y lo anota (RF-127, RF-128, RF-133).

    Returns:
        `True` si este fallo ha bloqueado el origen.
    """
    row = _row(session, origin, now)
    row.failures += 1
    row.updated_at = now
    if row.failures >= LOGIN_MAX_FAILURES:
        row.blocked_until = now + LOGIN_BLOCK
        record_incident(session, kind="origin_blocked", subject=origin,
                        reason=f"{LOGIN_MAX_FAILURES} intentos de acceso fallidos seguidos; bloqueado 15 minutos", now=now)
        return True
    return False


def record_success(session: Session, origin: str, now: datetime) -> None:
    """Un acceso correcto pone a cero el contador del origen (RF-131)."""
    row = _row(session, origin, now)
    row.failures, row.blocked_until, row.updated_at = 0, None, now
