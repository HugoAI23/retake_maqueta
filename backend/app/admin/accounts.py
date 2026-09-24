"""Cuenta única del administrador con Argon2id (spec 003: RF-121 a RF-123; H-7, D-12).

La contraseña nunca se guarda ni se registra: solo su *hash* Argon2id. La cuenta se crea o se
cambia fuera de la web, con `retake set-admin-password`.
"""

from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import AdminSession, AdminUser

_hasher = PasswordHasher()  # Argon2id con los parámetros recomendados por argon2-cffi
# Hash de una contraseña que nadie conoce: se verifica contra él cuando el usuario no existe,
# para que la respuesta tarde lo mismo y no delate qué usuarios existen (RF-126).
_DUMMY_HASH = _hasher.hash("retake-usuario-inexistente")


def set_admin_password(session: Session, username: str, password: str, now: datetime) -> None:
    """Crea la cuenta o sustituye su usuario y contraseña; cierra todas las sesiones abiertas.

    Raises:
        ValueError: si el usuario o la contraseña están vacíos.
    """
    if not username.strip() or not password:
        raise ValueError("El usuario y la contraseña no pueden estar vacíos.")
    user = session.get(AdminUser, 1)
    if user is None:
        session.add(AdminUser(id=1, username=username.strip(), password_hash=_hasher.hash(password), created_at=now))
    else:
        user.username, user.password_hash = username.strip(), _hasher.hash(password)
    session.execute(delete(AdminSession))
    session.flush()


def verify_login(session: Session, username: str, password: str) -> bool:
    """Comprueba usuario y contraseña, sin decir cuál de los dos falla (RF-126)."""
    user = session.scalar(select(AdminUser).where(AdminUser.username == username))
    try:
        _hasher.verify(user.password_hash if user else _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return user is not None
