"""Construcción de las respuestas de la API a partir de los datos resueltos."""

import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api import schemas as out
from app.api.freshness import live_last_success, match_is_stale
from app.db.models import (
    Championship,
    Event,
    Franchise,
    Identity,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    Placement,
    PlacementRoster,
    Player,
    PlayerGamertag,
    PlayerMapStats,
    RosterMembership,
    Season,
    Standing,
)
from app.db.models.matches import PLAYER_STAT_FIELDS
from app.db.queries import (
    championship_ids_for_player,
    current_season,
    finished_season_matches,
    guest_only_player_ids,
    is_current_season_player,
    is_free_agent,
    last_played_at,
    season_has_matches,
    visible,
)
from app.domain.ages import player_age
from app.domain.identities import identity_at
from app.domain.season_balance import counts, season_balances
from app.ingest.resolvers import franchise_identities


def utc(value: datetime | None) -> datetime | None:
    return None if value is None else value.astimezone(UTC)


def to_float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def pair(first, second) -> list | None:
    return None if first is None and second is None else [first, second]


def identity_out(identity: Identity | None) -> out.IdentityOut | None:
    if identity is None:
        return None
    return out.IdentityOut(
        id=str(identity.id), short_name=identity.short_name, abbreviation=identity.abbreviation,
        # Spec 003 (RF-65, RF-70): se muestra la copia propia; sin copia, el logo no está registrado.
        logo_url=f"/api/logos/{identity.logo_image_id}" if identity.logo_image_id else None,
        primary_color=identity.primary_color,
        secondary_color=identity.secondary_color, valid_from=utc(identity.valid_from),
        changed_at=utc(identity.changed_at),
    )


def identity_of_franchise_at(session: Session, franchise_id: uuid.UUID, instant: datetime) -> out.IdentityOut | None:
    """Identidad vigente de una franquicia en un instante (RF-12, R-4)."""
    version = identity_at(franchise_identities(session, franchise_id), instant)
    return identity_out(session.get(Identity, version.id)) if version else None


# --- Temporada, franquicias, eventos ------------------------------------------------------------

def season_view(season: Season) -> out.SeasonOut:
    return out.SeasonOut(year=season.year, name=season.name, started_at=utc(season.started_at),
                         changed_at=utc(season.changed_at))


def franchise_views(session: Session) -> list[out.FranchiseOut]:
    views = []
    # Los equipos invitados se ven solo en sus partidos (RF-117c de la 002; C-23).
    for franchise in session.scalars(select(Franchise).where(visible(Franchise, "franchise"), Franchise.is_guest.is_(False))):
        identities = session.scalars(
            select(Identity).where(Identity.franchise_id == franchise.id).order_by(Identity.valid_from)
        ).all()
        views.append(out.FranchiseOut(id=str(franchise.id), identities=[identity_out(i) for i in identities]))
    return sorted(views, key=lambda f: (f.identities[-1].short_name.casefold() if f.identities else ""))


def event_views(session: Session) -> list[out.EventOut]:
    season = current_season(session)
    if season is None:
        return []
    events = session.scalars(select(Event).where(Event.season_id == season.id, visible(Event, "event")).order_by(Event.name))
    return [out.EventOut(id=str(e.id), name=e.name, season_year=season.year, changed_at=utc(e.changed_at))
            for e in events]


# --- Jugadores ---------------------------------------------------------------------------------

def _current_team(session: Session, player_id: uuid.UUID, now: datetime) -> uuid.UUID | None:
    season = current_season(session)
    if season is None:
        return None
    return session.scalar(
        select(RosterMembership.franchise_id).where(
            RosterMembership.season_id == season.id,
            RosterMembership.player_id == player_id,
            or_(RosterMembership.from_date.is_(None), RosterMembership.from_date <= now),
            or_(RosterMembership.to_date.is_(None), RosterMembership.to_date > now),
        ).limit(1)
    )


def player_view(session: Session, player: Player, now: datetime) -> out.PlayerOut:
    age = player_age(player.birth_date, player.birth_year, now)
    team = _current_team(session, player.id, now)
    previous = session.scalars(
        select(PlayerGamertag.gamertag).where(PlayerGamertag.player_id == player.id).order_by(PlayerGamertag.position)
    ).all()
    return out.PlayerOut(
        id=str(player.id),
        current_gamertag=player.current_gamertag,
        previous_gamertags=list(previous),
        real_name=player.real_name,
        country=player.country,
        age=out.AgeOut(min=age.min, max=age.max) if age else None,
        role=player.role,
        team_franchise_id=str(team) if team else None,
        team_is_guest=bool(team) and session.get(Franchise, team).is_guest,
        is_current_season=is_current_season_player(session, player.id),
        is_free_agent=is_free_agent(session, player.id, now),
        championship_ids=[str(cid) for cid in championship_ids_for_player(session, player.id)],
        changed_at=utc(player.changed_at),
    )


def player_views(session: Session, now: datetime) -> list[out.PlayerOut]:
    # Los jugadores que solo jugaron con invitados se ven solo en sus partidos (RF-117c de la 002; C-23).
    guests_only = guest_only_player_ids(session)
    players = sorted((p for p in session.scalars(select(Player).where(visible(Player, "player"))) if p.id not in guests_only),
                     key=lambda p: p.current_gamertag.casefold())
    return [player_view(session, p, now) for p in players]


# --- Partidos ----------------------------------------------------------------------------------

def _stats_view(stats: PlayerMapStats) -> out.StatsOut:
    values = {name: getattr(stats, name) for name in PLAYER_STAT_FIELDS}
    values["kd"] = to_float(values["kd"])
    return out.StatsOut(
        player_id=str(stats.player_id),
        franchise_id=str(stats.franchise_id) if stats.franchise_id else None,
        is_substitute=stats.is_substitute,
        corrected_fields=list(stats.corrected_fields),
        changed_at=utc(stats.changed_at),
        **values,
    )


def _map_view(session: Session, game_map: MatchMap) -> out.MatchMapOut:
    stats = session.scalars(
        select(PlayerMapStats).join(Player, Player.id == PlayerMapStats.player_id)
        .where(PlayerMapStats.map_id == game_map.id).order_by(Player.current_gamertag)
    ).all()
    return out.MatchMapOut(
        position=game_map.position, mode=game_map.mode, map_name=game_map.map_name, played=game_map.played,
        score=pair(game_map.score_1, game_map.score_2) if game_map.played else None,
        winner_side=game_map.winner_side, corrected_fields=list(game_map.corrected_fields),
        stats=[_stats_view(s) for s in stats],
        changed_at=utc(game_map.changed_at),
    )


def match_view(session: Session, match: Match, now: datetime, live_success: dict | None = None) -> out.MatchOut:
    schedule = [utc(s) for s in session.scalars(
        select(MatchSchedule.scheduled_at).where(MatchSchedule.match_id == match.id).order_by(MatchSchedule.seq))]
    scheduled_at = schedule[-1] if schedule else None
    slots_by_side = {s.side: s for s in session.scalars(select(MatchSlot).where(MatchSlot.match_id == match.id))}
    slots = []
    for side in (1, 2):
        slot = slots_by_side.get(side)
        franchise_id = slot.franchise_id if slot else None
        origin = (
            out.OriginOut(match_id=str(slot.origin_match_id), outcome=slot.origin_outcome)
            if slot is not None and slot.origin_match_id is not None else None
        )
        slots.append(out.SlotOut(
            franchise_id=str(franchise_id) if franchise_id else None,
            identity=identity_of_franchise_at(session, franchise_id, scheduled_at or now) if franchise_id else None,
            origin=origin,
            is_guest=bool(franchise_id) and session.get(Franchise, franchise_id).is_guest,
        ))
    maps_query = select(MatchMap).where(MatchMap.match_id == match.id).order_by(MatchMap.position)
    if match.status != "finished":
        maps_query = maps_query.where(MatchMap.played.is_(True))  # los no jugados, solo al finalizar (RF-92)
    event = session.get(Event, match.event_id)
    return out.MatchOut(
        id=str(match.id), event_id=str(event.id), event_name=event.name, phase=match.phase,
        best_of=match.best_of, status=match.status, scheduled_at=scheduled_at, schedule_history=schedule,
        slots=slots,
        maps_won=pair(match.maps_won_1, match.maps_won_2),
        live_map=out.LiveMapOut(mode=match.live_mode, score=pair(match.live_score_1, match.live_score_2))
        if match.status == "live" else None,
        winner_side=match.winner_side, corrected_fields=list(match.corrected_fields),
        maps=[_map_view(session, m) for m in session.scalars(maps_query)],
        changed_at=utc(match.changed_at),
        is_stale=match_is_stale(session, match, live_success),
    )


def match_views(session: Session, now: datetime) -> list[out.MatchOut]:
    season = current_season(session)
    if season is None:
        return []
    matches = session.scalars(select(Match).join(Event, Event.id == Match.event_id)
                              .where(Event.season_id == season.id, visible(Match, "match")))
    live_success = live_last_success(session)
    views = [match_view(session, m, now, live_success) for m in matches]
    far_future = datetime.max.replace(tzinfo=UTC)
    return sorted(views, key=lambda m: (m.scheduled_at or far_future, m.id))


# --- Tabla de posiciones e historial ------------------------------------------------------------

def _record_out(record) -> out.RecordOut:
    return out.RecordOut(won=record.won, lost=record.lost)


def standing_views(session: Session, now: datetime) -> list[out.StandingOut]:
    season = current_season(session)
    if season is None:
        return []
    # Un invitado nunca está en la tabla (RF-117c de la 002; C-23).
    rows = session.scalars(select(Standing).join(Franchise, Franchise.id == Standing.franchise_id)
                           .where(Standing.season_id == season.id, Franchise.is_guest.is_(False))).all()
    # Balance de series y mapas (RF-136 a RF-139 de la 002; C-29).
    matches = finished_season_matches(session, season.id)
    balances = season_balances([row.franchise_id for row in rows], [m.result for m in matches],
                               season_has_matches(session, season.id))
    # Última actualización de cada fila: la fila o sus partidos contados (RF-53e de la 004, D-7).
    changed = {row.franchise_id: row.changed_at for row in rows}
    for m in (m for m in matches if counts(m.result) and m.changed_at is not None):
        for franchise_id in m.result.sides:
            if franchise_id in changed and (changed[franchise_id] is None or m.changed_at > changed[franchise_id]):
                changed[franchise_id] = m.changed_at
    # Cada fila lleva la identidad de su último partido jugado de la temporada o, si no ha jugado
    # ninguno, la vigente (RF-41a, RF-41b de la 004): el nombre con el que jugó esa temporada.
    played_at = last_played_at(session, season.id)
    views = []
    for row in rows:
        balance = balances[row.franchise_id] if balances is not None else None
        views.append(out.StandingOut(
            franchise_id=str(row.franchise_id),
            identity=identity_of_franchise_at(session, row.franchise_id, played_at.get(row.franchise_id, now)),
            position=row.position, points=row.points,
            series=_record_out(balance.series) if balance else None,
            maps=_record_out(balance.maps) if balance else None,
            changed_at=utc(changed[row.franchise_id]),
        ))
    return sorted(views, key=lambda v: (v.position is None, v.position or 0,
                                        v.identity.short_name.casefold() if v.identity else ""))


def _place_key(place: str | None) -> tuple:
    """Orden de la clasificación: por número (el de inicio en un rango), después DQ y los desconocidos."""
    if place is None:
        return (2, 0)
    match = re.match(r"\s*(\d+)", place)
    return (0, int(match.group(1))) if match else (1, 0)


def championship_views(session: Session) -> list[out.ChampionshipOut]:
    views = []
    championships = session.scalars(
        select(Championship).where(Championship.completed.is_(True)).order_by(Championship.year.desc()))
    for championship in championships:
        placements = sorted(
            session.scalars(select(Placement).where(Placement.championship_id == championship.id)),
            key=lambda p: _place_key(p.place),
        )
        placement_views = []
        for placement in placements:
            roster = session.execute(
                select(PlacementRoster, Player.current_gamertag)
                .join(Player, Player.id == PlacementRoster.player_id)
                .where(PlacementRoster.placement_id == placement.id)
                .order_by(PlacementRoster.gamertag_at_final)
            ).all()
            placement_views.append(out.PlacementOut(
                franchise_id=str(placement.franchise_id),
                identity=identity_out(session.get(Identity, placement.identity_id)) if placement.identity_id else None,
                place=placement.place, is_dq=placement.is_dq,
                prize_usd=to_float(placement.prize_usd), pool_percent=to_float(placement.pool_percent),
                roster=[out.RosterEntryOut(player_id=str(entry.player_id), gamertag_at_final=entry.gamertag_at_final,
                                           current_gamertag=gamertag) for entry, gamertag in roster],
                corrected_fields=list(placement.corrected_fields),
                changed_at=utc(placement.changed_at),
            ))
        views.append(out.ChampionshipOut(
            id=str(championship.id), year=championship.year, competition=championship.competition,
            game_name=championship.game_name, game_abbreviation=championship.game_abbreviation,
            final_date=championship.final_date, placements=placement_views,
            changed_at=utc(championship.changed_at),
        ))
    return views
