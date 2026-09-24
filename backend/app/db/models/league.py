"""Temporadas, eventos, franquicias e identidades (plan de la spec 002, §3.2)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.types import changed_at_column, uuid_pk


class Season(Base):
    """Temporada, identificada por su año oficial (RF-52).

    `started_at` se fija cuando el primer partido oficial de la temporada pasa a
    `en vivo` y no se borra nunca (RF-3, RF-123). La temporada actual se calcula a
    partir de este campo, no se guarda (plan D-7).
    """

    __tablename__ = "season"

    id: Mapped[uuid.UUID] = uuid_pk()
    year: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    changed_at: Mapped[datetime | None] = changed_at_column()


class Event(Base):
    """Evento de la temporada, con el nombre tal como lo publica la fuente (RF-30, RF-61)."""

    __tablename__ = "event"

    id: Mapped[uuid.UUID] = uuid_pk()
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("season.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    changed_at: Mapped[datetime | None] = changed_at_column()


class Franchise(Base):
    """Franquicia: sigue siendo la misma aunque cambie de nombre, dueño o ciudad (RF-10, RF-114).

    Sus datos visibles viven en sus identidades.

    - `is_guest`: equipo invitado, que no es de la CDL y juega un evento de la CDL (RF-117a; cambio
      C-23 de la spec 003). Se ve solo en sus partidos (RF-117c).
    - `guest_checked_at`: última consulta de la ficha del invitado y de sus jugadores, que van una
      vez al mes (RF-18b de la 003).
    """

    __tablename__ = "franchise"

    id: Mapped[uuid.UUID] = uuid_pk()
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    guest_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Identity(Base):
    """Nombre corto, abreviatura, logo y colores de una franquicia desde una fecha (RF-11, RF-74).

    Cualquier cambio de esos cinco datos crea una identidad nueva (RF-73).

    `logo_image_id` apunta a la copia propia del logo (spec 003, RF-65); `logo_url`
    conserva la dirección original publicada por la fuente.
    """

    __tablename__ = "identity"
    __table_args__ = (UniqueConstraint("franchise_id", "valid_from"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    franchise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("franchise.id", ondelete="CASCADE"))
    short_name: Mapped[str] = mapped_column(String(255))
    abbreviation: Mapped[str | None] = mapped_column(String(32))
    logo_url: Mapped[str | None] = mapped_column(String(2048))
    primary_color: Mapped[str | None] = mapped_column(String(16))
    secondary_color: Mapped[str | None] = mapped_column(String(16))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    logo_image_id: Mapped[str | None] = mapped_column(ForeignKey("logo_image.id", ondelete="SET NULL"))
    changed_at: Mapped[datetime | None] = changed_at_column()
