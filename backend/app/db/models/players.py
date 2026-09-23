"""Jugadores, sus gamertags y sus rosters (plan de la spec 002, §3.2)."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.types import ROLES, closed_values, uuid_pk


class Player(Base):
    """Jugador: una persona, aunque haya usado varios gamertags (RF-18).

    - La fecha y el año de nacimiento solo se usan para calcular la edad en el
      servidor; la API nunca los devuelve (RF-24, plan D-10).
    - `role` lo asigna Retake con el archivo de curación; nulo = `Sin rol` (RF-26, RF-27).
    - `personal_data_removed` indica que se atendió una petición de retirada (RF-78).
    """

    __tablename__ = "player"

    id: Mapped[uuid.UUID] = uuid_pk()
    current_gamertag: Mapped[str] = mapped_column(String(255))
    real_name: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(64))
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_year: Mapped[int | None] = mapped_column(Integer)
    birth_year_is_approx: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    retired: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    role: Mapped[str | None] = mapped_column(closed_values("role", ROLES))
    personal_data_removed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)


class PlayerGamertag(Base):
    """Gamertag que ha usado un jugador, en orden de uso (RF-17)."""

    __tablename__ = "player_gamertag"
    __table_args__ = (UniqueConstraint("player_id", "position"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player.id", ondelete="CASCADE"))
    gamertag: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer)


class RosterMembership(Base):
    """Pertenencia de un jugador al roster de una franquicia en la temporada actual.

    Solo se crea a partir de registros de roster de las fuentes, nunca por haber
    jugado un partido: así un suplente no entra en el roster (RF-104).
    """

    __tablename__ = "roster_membership"

    id: Mapped[uuid.UUID] = uuid_pk()
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("season.id", ondelete="CASCADE"))
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player.id", ondelete="CASCADE"))
    franchise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("franchise.id", ondelete="CASCADE"))
    from_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    to_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
