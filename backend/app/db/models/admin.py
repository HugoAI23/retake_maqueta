"""Cuenta, sesiones y bloqueo por origen del administrador (plan de la spec 003, §4 y §9)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdminUser(Base):
    """La única cuenta con acceso a la página de administración (RF-121).

    - `id` siempre vale 1: la base de datos no admite una segunda cuenta.
    - `password_hash` es un *hash* Argon2id; la contraseña nunca se guarda (H-7, RF-123).
    - La cuenta se crea fuera de la web con `retake set-admin-password` (RF-122, D-12).
    """

    __tablename__ = "admin_user"
    __table_args__ = (CheckConstraint("id = 1", name="single_account"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, server_default=text("1"), default=1)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AdminSession(Base):
    """Sesión abierta del administrador (RF-125, RF-134 a RF-138; decisión H-8).

    Solo se guarda la huella SHA-256 del identificador aleatorio de la cookie: quien lea
    la base de datos no puede usar una sesión. Puede haber varias a la vez (RF-135).
    """

    __tablename__ = "admin_session"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    origin: Mapped[str | None] = mapped_column(String(64))


class LoginOrigin(Base):
    """Intentos fallidos seguidos y bloqueo de un origen (RF-127 a RF-133, plan D-10).

    El bloqueo es por origen (dirección del cliente), no por cuenta: un atacante no puede
    dejar al administrador sin acceso desde otros sitios (decisión Q-33 de la spec).
    """

    __tablename__ = "login_origin"
    __table_args__ = (CheckConstraint("failures >= 0", name="failures_not_negative"),)

    origin: Mapped[str] = mapped_column(String(64), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, server_default=text("0"), default=0)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
