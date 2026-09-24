"""Partidos, horarios, equipos, mapas y estadísticas (plan de la spec 002, §3.2 y §3.4)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.types import (
    MATCH_STATUSES,
    ORIGIN_OUTCOMES,
    PHASES,
    changed_at_column,
    closed_values,
    corrected_fields_column,
    uuid_pk,
)

# Estadísticas de jugador por mapa (RF-41 a RF-44): 5 comunes + 2 de Hardpoint +
# 4 de Search & Destroy + 2 de Overload. Todas admiten nulo = no publicada (RF-65).
PLAYER_STAT_FIELDS = (
    "kills",
    "deaths",
    "kd",
    "damage",
    "assists",
    "hill_time",
    "contested_hill_time",
    "first_bloods",
    "first_deaths",
    "plants",
    "defuses",
    "zone_captures",
    "overloads",
)


class Match(Base):
    """Partido: enfrentamiento completo al mejor de N mapas (glosario de la spec).

    - `phase` nula = fase desconocida (RF-134).
    - `status` solo avanza: scheduled → live → finished (RF-62, plan §3.4).
    - `maps_won_*`, `live_*` y `winner_side` se rellenan según el estado (RF-36 a RF-39).
    - Spec 003: `stats_complete_at` (todas sus estadísticas registradas; abre la ventana
      de revisión de 7 días, RF-19 a RF-21) y `disappeared_at` (desaparecido de las
      fuentes, RF-50 a RF-52).
    - Spec 003 (C-13): `week`, número de semana de un partido de fase `week`; el publicado
      por una fuente o, si no hay, el calculado (RF-31 de la 002 revisado).
    """

    __tablename__ = "match"
    __table_args__ = (
        CheckConstraint("best_of > 0", name="best_of_positive"),
        CheckConstraint("winner_side IN (1, 2)", name="winner_side_valid"),
        CheckConstraint(
            "maps_won_1 >= 0 AND maps_won_2 >= 0 AND live_score_1 >= 0 AND live_score_2 >= 0",
            name="scores_not_negative",
        ),
        CheckConstraint("week > 0", name="week_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"))
    phase: Mapped[str | None] = mapped_column(closed_values("phase", PHASES))
    best_of: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(
        closed_values("match_status", MATCH_STATUSES), server_default="scheduled", default="scheduled"
    )
    went_live_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    maps_won_1: Mapped[int | None] = mapped_column(SmallInteger)
    maps_won_2: Mapped[int | None] = mapped_column(SmallInteger)
    live_mode: Mapped[str | None] = mapped_column(String(64))
    live_score_1: Mapped[int | None] = mapped_column(Integer)
    live_score_2: Mapped[int | None] = mapped_column(Integer)
    winner_side: Mapped[int | None] = mapped_column(SmallInteger)
    corrected_fields: Mapped[list[str]] = corrected_fields_column()
    stats_complete_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disappeared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    week: Mapped[int | None] = mapped_column(SmallInteger)
    changed_at: Mapped[datetime | None] = changed_at_column()


class MatchSchedule(Base):
    """Cada fecha y hora de inicio que ha tenido un partido, en orden; manda la última (RF-87, RF-88)."""

    __tablename__ = "match_schedule"
    __table_args__ = (UniqueConstraint("match_id", "seq"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match.id", ondelete="CASCADE"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    seq: Mapped[int] = mapped_column(Integer)


class MatchSlot(Base):
    """Uno de los dos lados de un partido: equipo conocido u origen si aún no se conoce (RF-32, RF-84)."""

    __tablename__ = "match_slot"
    __table_args__ = (
        UniqueConstraint("match_id", "side"),
        CheckConstraint("side IN (1, 2)", name="side_valid"),
        CheckConstraint(
            "franchise_id IS NULL OR origin_match_id IS NULL", name="team_or_origin"
        ),
        # Un origen siempre lleva su resultado. Al revés no se exige: si se borra el partido de
        # origen, la clave foránea lo deja nulo y el resultado sobrante no cuenta (sin origen).
        CheckConstraint(
            "origin_match_id IS NULL OR origin_outcome IS NOT NULL", name="origin_complete"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match.id", ondelete="CASCADE"))
    side: Mapped[int] = mapped_column(SmallInteger)
    franchise_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("franchise.id", ondelete="SET NULL"))
    origin_match_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("match.id", ondelete="SET NULL"))
    origin_outcome: Mapped[str | None] = mapped_column(closed_values("origin_outcome", ORIGIN_OUTCOMES))


class MatchMap(Base):
    """Mapa de un partido: jugado (con ganador) o no jugado (RF-40, RF-92).

    El modo se guarda tal como lo publica la fuente, también si no es uno de los
    tres conocidos (RF-95).
    """

    __tablename__ = "match_map"
    __table_args__ = (
        UniqueConstraint("match_id", "position"),
        CheckConstraint("position > 0", name="position_positive"),
        CheckConstraint("winner_side IN (1, 2)", name="winner_side_valid"),
        CheckConstraint("score_1 >= 0 AND score_2 >= 0", name="scores_not_negative"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(SmallInteger)
    mode: Mapped[str | None] = mapped_column(String(64))
    map_name: Mapped[str | None] = mapped_column(String(128))
    played: Mapped[bool] = mapped_column(Boolean)
    score_1: Mapped[int | None] = mapped_column(Integer)
    score_2: Mapped[int | None] = mapped_column(Integer)
    winner_side: Mapped[int | None] = mapped_column(SmallInteger)
    corrected_fields: Mapped[list[str]] = corrected_fields_column()
    changed_at: Mapped[datetime | None] = changed_at_column()


class PlayerMapStats(Base):
    """Estadísticas de un jugador en un mapa jugado (RF-41 a RF-45).

    - `franchise_id`: equipo con el que jugó ese partido (RF-29).
    - `is_substitute`: jugó con un equipo a cuyo roster no pertenecía (RF-103).
    - Cada estadística es nula si la fuente no la publica: nulo ≠ 0 (RF-65, plan D-8).
    """

    __tablename__ = "player_map_stats"
    __table_args__ = (
        UniqueConstraint("map_id", "player_id"),
        CheckConstraint(
            " AND ".join(f"{field} >= 0" for field in PLAYER_STAT_FIELDS),
            name="stats_not_negative",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    map_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match_map.id", ondelete="CASCADE"))
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player.id", ondelete="CASCADE"))
    franchise_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("franchise.id", ondelete="SET NULL"))
    is_substitute: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    kills: Mapped[int | None] = mapped_column(Integer)
    deaths: Mapped[int | None] = mapped_column(Integer)
    kd: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    damage: Mapped[int | None] = mapped_column(Integer)
    assists: Mapped[int | None] = mapped_column(Integer)
    hill_time: Mapped[int | None] = mapped_column(Integer)  # segundos
    contested_hill_time: Mapped[int | None] = mapped_column(Integer)  # segundos
    first_bloods: Mapped[int | None] = mapped_column(Integer)
    first_deaths: Mapped[int | None] = mapped_column(Integer)
    plants: Mapped[int | None] = mapped_column(Integer)
    defuses: Mapped[int | None] = mapped_column(Integer)
    zone_captures: Mapped[int | None] = mapped_column(Integer)
    overloads: Mapped[int | None] = mapped_column(Integer)
    corrected_fields: Mapped[list[str]] = corrected_fields_column()
    changed_at: Mapped[datetime | None] = changed_at_column()
