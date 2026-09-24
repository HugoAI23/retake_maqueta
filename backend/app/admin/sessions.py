"""Sesiones del administrador en el servidor (spec 003: RF-125, RF-134 a RF-138; plan §9, H-8).

El identificador es aleatorio de 32 bytes y viaja solo en la cookie; en la base de datos se
guarda su huella SHA-256, así que quien la lea no puede usar una sesión. Caducan a las 8 horas y
puede haber varias a la vez.
"""

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import AdminSession
from app.domain.vocabulary import SESSION_DURATION

COOKIE_NAME = "retake_admin"
COOKIE_PATH = "/api/admin"


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def open_session(session: Session, now: datetime, origin: str | None) -> str:
    """Abre una sesión y devuelve su identificador (solo para la cookie)."""
    token = secrets.token_urlsafe(32)
    session.add(AdminSession(token_hash=_hash(token), created_at=now, expires_at=now + SESSION_DURATION,
                             last_seen_at=now, origin=origin))
    session.flush()
    return token


def valid_session(session: Session, token: str | None, now: datetime) -> AdminSession | None:
    """La sesión de la cookie si sigue abierta; una caducada se borra (RF-134, RF-137)."""
    if not token:
        return None
    row = session.get(AdminSession, _hash(token))
    if row is None:
        return None
    if row.expires_at <= now:
        session.delete(row)
        session.flush()
        return None
    row.last_seen_at = now
    return row


def close_session(session: Session, token: str | None) -> None:
    """Cierra la sesión en el servidor (RF-138)."""
    if token:
        session.execute(delete(AdminSession).where(AdminSession.token_hash == _hash(token)))
