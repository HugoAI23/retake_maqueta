"""Consultas de estado calculado sobre los datos resueltos (T-038)."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.orm import Session

from app.db.models import (
    Championship,
    Event,
    ExternalRef,
    Franchise,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    Placement,
    PlacementRoster,
    PlayerMapStats,
    RosterMembership,
    Season,
)
from app.domain.season_balance import FinishedMatch
from app.domain.seasons import current_season_year


def guest_only_player_ids(session: Session) -> set[uuid.UUID]:
    """Jugadores que solo aparecen con equipos invitados (RF-117c de la 002; cambio C-23 de la 003).

    Se ven solo en sus partidos, no en las listas. Un jugador con algún roster o partido con una
    franquicia de la liga, o con historial de campeonatos, sigue en las listas.
    """
    def linked(guest: bool) -> set[uuid.UUID]:
        rosters = select(RosterMembership.player_id).join(Franchise, Franchise.id == RosterMembership.franchise_id) \
            .where(Franchise.is_guest.is_(guest))
        stats = select(PlayerMapStats.player_id).join(Franchise, Franchise.id == PlayerMapStats.franchise_id) \
            .where(Franchise.is_guest.is_(guest))
        return set(session.scalars(rosters.union(stats)))

    league = linked(False) | set(session.scalars(select(PlacementRoster.player_id)))
    return linked(True) - league


def visible(model, kind: str):
    """Condición: la fila no está oculta por la retención (spec 003: RF-55, nota C-14).

    Oculta = todas sus referencias están retenidas. Solo se aplica a las listas de la temporada
    actual; el historial usa también los registros retenidos.
    """
    refs = ExternalRef.kind == kind, ExternalRef.entity_id == model.id
    return not_(and_(exists().where(*refs, ExternalRef.retained_since.is_not(None)),
                     ~exists().where(*refs, ExternalRef.retained_since.is_(None))))


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


# --- Balance e identidad de la tabla de posiciones (spec 004) --------------------------------------

@dataclass(frozen=True)
class SeasonMatch:
    """Partido `finalizado` de la temporada, con el instante de su último cambio (RF-53e de la 004)."""

    result: FinishedMatch
    changed_at: datetime | None


def _season_matches(season_id: uuid.UUID):
    """Partidos visibles de una temporada (los ocultos por la retención no cuentan, como en la lista)."""
    return (select(Match).join(Event, Event.id == Match.event_id)
            .where(Event.season_id == season_id, visible(Match, "match")))


def season_has_matches(session: Session, season_id: uuid.UUID) -> bool:
    """Si la temporada tiene algún partido registrado, en cualquier estado (decisión D-6 de la 004)."""
    return bool(session.scalar(select(_season_matches(season_id).exists())))


def finished_season_matches(session: Session, season_id: uuid.UUID) -> list[SeasonMatch]:
    """Partidos `finalizado` de la temporada con la franquicia de cada lado, el ganador y el marcador.

    Es la entrada del balance de series y mapas (RF-136 a RF-138a de la 002).
    """
    matches = session.scalars(_season_matches(season_id).where(Match.status == "finished")).all()
    sides = {(match_id, side): franchise_id for match_id, side, franchise_id in session.execute(
        select(MatchSlot.match_id, MatchSlot.side, MatchSlot.franchise_id)
        .where(MatchSlot.match_id.in_([m.id for m in matches])))}
    return [
        SeasonMatch(
            result=FinishedMatch(sides=(sides.get((m.id, 1)), sides.get((m.id, 2))), winner_side=m.winner_side,
                                 maps_won=(m.maps_won_1, m.maps_won_2)),
            changed_at=m.changed_at,
        )
        for m in matches
    ]


def last_played_at(session: Session, season_id: uuid.UUID) -> dict[uuid.UUID, datetime]:
    """Hora programada del último partido `en vivo` o `finalizado` de cada franquicia en la temporada.

    Cuenta la última hora programada de cada partido (la de su reprogramación más reciente). Las
    franquicias que no han jugado ninguno no aparecen (RF-41a, RF-41b de la 004).
    """
    last_seq = (select(MatchSchedule.match_id, func.max(MatchSchedule.seq).label("seq"))
                .group_by(MatchSchedule.match_id).subquery())
    played = _season_matches(season_id).where(Match.status.in_(("live", "finished"))).subquery()
    rows = session.execute(
        select(MatchSlot.franchise_id, func.max(MatchSchedule.scheduled_at))
        .join(played, played.c.id == MatchSlot.match_id)
        .join(last_seq, last_seq.c.match_id == MatchSlot.match_id)
        .join(MatchSchedule, and_(MatchSchedule.match_id == last_seq.c.match_id, MatchSchedule.seq == last_seq.c.seq))
        .where(MatchSlot.franchise_id.is_not(None))
        .group_by(MatchSlot.franchise_id)
    )
    return dict(rows.tuples().all())
