"""Consultas de estado calculado sobre los datos resueltos (T-038)."""

import uuid
from datetime import datetime

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.db.models import (
    Championship,
    Event,
    Match,
    MatchMap,
    Placement,
    PlacementRoster,
    PlayerMapStats,
    RosterMembership,
    Season,
)
from app.domain.seasons import current_season_year


def current_season(session: Session) -> Season | None:
    """Temporada actual: la más reciente que ya empezó (RF-2, RF-3)."""
    year = current_season_year(dict(session.execute(select(Season.year, Season.started_at)).all()))
    return None if year is None else session.scalar(select(Season).where(Season.year == year))


def is_current_season_player(session: Session, player_id: uuid.UUID) -> bool:
    """Jugador de la temporada actual: está en un roster o ha jugado al menos un partido (RF-102, RF-105)."""
    season = current_season(session)
    if season is None:
        return False
    in_roster = exists().where(RosterMembership.season_id == season.id, RosterMembership.player_id == player_id)
    played = (
        exists()
        .where(PlayerMapStats.player_id == player_id)
        .where(MatchMap.id == PlayerMapStats.map_id, Match.id == MatchMap.match_id, Event.id == Match.event_id)
        .where(Event.season_id == season.id)
    )
    return bool(session.scalar(select(or_(in_roster, played))))


def is_free_agent(session: Session, player_id: uuid.UUID, now: datetime) -> bool:
    """Agente libre: jugador de la temporada actual sin ningún roster vigente en `now` (RF-106)."""
    season = current_season(session)
    if season is None or not is_current_season_player(session, player_id):
        return False
    open_roster = exists().where(
        RosterMembership.season_id == season.id,
        RosterMembership.player_id == player_id,
        or_(RosterMembership.from_date.is_(None), RosterMembership.from_date <= now),
        or_(RosterMembership.to_date.is_(None), RosterMembership.to_date > now),
    )
    return not session.scalar(select(open_roster))


def championship_ids_for_player(session: Session, player_id: uuid.UUID) -> list[uuid.UUID]:
    """Campeonatos terminados del historial en cuyo roster estuvo el jugador (RF-20)."""
    return list(session.scalars(
        select(Championship.id)
        .join(Placement, Placement.championship_id == Championship.id)
        .join(PlacementRoster, PlacementRoster.placement_id == Placement.id)
        .where(PlacementRoster.player_id == player_id, Championship.completed.is_(True))
        .distinct()
        .order_by(Championship.id)
    ))
