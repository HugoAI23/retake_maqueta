"""Tabla de posiciones e historial de campeonatos mundiales (plan de la spec 002, §3.2)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.types import corrected_fields_column, uuid_pk


class Standing(Base):
    """Posición y puntos CDL de una franquicia, tal como se publican (RF-49, RF-50, RF-122).

    Dos equipos pueden compartir `position` si así se publica: no se desempata.
    """

    __tablename__ = "standing"
    __table_args__ = (
        UniqueConstraint("season_id", "franchise_id"),
        CheckConstraint("position > 0", name="position_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("season.id", ondelete="CASCADE"))
    franchise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("franchise.id", ondelete="CASCADE"))
    position: Mapped[int | None] = mapped_column(Integer)
    points: Mapped[int | None] = mapped_column(Integer)


class Championship(Base):
    """Campeonato mundial de un año (RF-4, RF-54).

    Solo se expone si `completed` es verdadero: la temporada en curso no entra en
    el historial hasta que termina su final (RF-55).
    """

    __tablename__ = "championship"

    id: Mapped[uuid.UUID] = uuid_pk()
    year: Mapped[int] = mapped_column(Integer, unique=True)
    competition: Mapped[str | None] = mapped_column(String(128))
    game_name: Mapped[str | None] = mapped_column(String(128))
    game_abbreviation: Mapped[str | None] = mapped_column(String(16))
    final_date: Mapped[date | None] = mapped_column(Date)
    completed: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)


class Placement(Base):
    """Clasificación final de un equipo en un campeonato: **una fila por equipo** (RF-5, RF-7).

    - `place` es el texto publicado: `1`, `9-12` o `DQ` (RF-8, RF-9).
    - El premio es del equipo y nunca se reparte por jugador (RF-7).
    - Los datos que falten quedan nulos (RF-119).
    """

    __tablename__ = "placement"
    __table_args__ = (
        UniqueConstraint("championship_id", "franchise_id"),
        CheckConstraint("prize_usd >= 0", name="prize_not_negative"),
        CheckConstraint("pool_percent >= 0 AND pool_percent <= 100", name="pool_percent_range"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    championship_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("championship.id", ondelete="CASCADE"))
    franchise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("franchise.id", ondelete="CASCADE"))
    identity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("identity.id", ondelete="SET NULL"))
    published_team_name: Mapped[str | None] = mapped_column(String(255))
    place: Mapped[str | None] = mapped_column(String(16))
    is_dq: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    prize_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    pool_percent: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    corrected_fields: Mapped[list[str]] = corrected_fields_column()


class PlacementRoster(Base):
    """Jugador del roster de un equipo en un campeonato, con el gamertag que usaba entonces (RF-6, RF-59)."""

    __tablename__ = "placement_roster"
    __table_args__ = (UniqueConstraint("placement_id", "player_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placement.id", ondelete="CASCADE"))
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player.id", ondelete="CASCADE"))
    gamertag_at_final: Mapped[str | None] = mapped_column(String(255))
