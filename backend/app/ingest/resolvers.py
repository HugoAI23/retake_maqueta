"""Valor resuelto de cada tipo de entidad (plan de la spec 002, §3.3 a §3.6).

Cada función recalcula una entidad **a partir de las observaciones** de todas sus
referencias, nunca del registro que acaba de llegar. Así, recalcular una entidad
(tras una unión, una separación o la curación) siempre da el mismo resultado.

Lo que no se puede recalcular se conserva en la propia fila: el estado del partido
(que nunca retrocede), su historial de horarios, el inicio de la temporada, las
identidades y las correcciones.
"""

import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import delete, exists, select, update
from sqlalchemy.orm import Session

from app.curation.loader import Curation
from app.db.models import (
    Championship,
    Event,
    ExternalRef,
    Franchise,
    Identity,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    Observation,
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
from app.domain.ages import approx_birth_year
from app.domain.corrections import add_corrected_field, is_correction
from app.domain.identities import (
    IdentityData,
    IdentityVersion,
    identity_at,
    identity_for_championship,
    identity_valid_from,
    needs_new_identity,
)
from app.domain.match_state import StatusChange, apply_source_status
from app.domain.phases import normalize_phase
from app.domain.priority import STANDINGS_PRIORITY
from app.domain.seasons import current_season_year
from app.domain.validation import is_valid_maps_won
from app.ingest.store import ObservationIndex, entity_for, refs_of_entity, require_entity


class IngestError(ValueError):
    """Un registro no se puede aplicar (p. ej. falta un dato imprescindible)."""


# Datos personales de un jugador (RF-21 a RF-23, RF-77, RF-78).
PERSONAL_FIELDS = ("real_name", "country", "birth_date", "birth_year", "age")

# Estadísticas comunes y propias de cada modo (RF-41 a RF-44). Un modo desconocido
# solo registra las comunes (RF-95).
COMMON_STATS = ("kills", "deaths", "kd", "damage", "assists")
MODE_STATS = {
    "hardpoint": ("hill_time", "contested_hill_time"),
    "search and destroy": ("first_bloods", "first_deaths", "plants", "defuses"),
    "overload": ("zone_captures", "overloads"),
}


@dataclass
class IngestContext:
    """Estado de una ingesta en curso.

    Attributes:
        created: Observaciones creadas por el registro actual `(ref_id, campo)`; sirve
            para saber si un dato llega por primera vez (RF-98).
        detect_corrections: Falso al recalcular por una unión, separación o curación:
            eso no es un cambio de la fuente (RF-96).
        pending_rollover: Año de la temporada que acaba de empezar, si hay que hacer el
            cambio de temporada al terminar el registro.
    """

    session: Session
    curation: Curation
    created: set[tuple[int, str]] = field(default_factory=set)
    detect_corrections: bool = True
    pending_rollover: int | None = None


@contextmanager
def corrections_off(ctx: IngestContext):
    previous = ctx.detect_corrections
    ctx.detect_corrections = False
    try:
        yield
    finally:
        ctx.detect_corrections = previous


# --- Conversión de valores guardados en JSON ------------------------------------------------


def to_int(value: object) -> int | None:
    return None if value is None else int(value)


def to_decimal(value: object) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def to_datetime(value: object) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def to_date(value: object) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def set_field(ctx, row, attr, new, *, closed: bool, index: ObservationIndex, is_new: bool) -> None:
    """Asigna un campo y lo marca como corregido si procede (RF-96 a RF-98)."""
    old = getattr(row, attr)
    if (
        not is_new
        and ctx.detect_corrections
        and is_correction(
            entity_closed=closed,
            had_previous_observation=index.had_previous(attr, ctx.created),
            old_value=old,
            new_value=new,
        )
    ):
        row.corrected_fields = add_corrected_field(list(row.corrected_fields or []), attr)
    setattr(row, attr, new)


def _own_index(ctx: IngestContext, ref: ExternalRef) -> ObservationIndex:
    return ObservationIndex(ctx.session, [ref])


def _link(ctx: IngestContext, ref: ExternalRef, row) -> tuple[list[ExternalRef], ObservationIndex]:
    """Enlaza la referencia con la fila y devuelve el grupo completo y sus observaciones."""
    ref.entity_id = row.id
    ctx.session.flush()
    refs = refs_of_entity(ctx.session, ref.kind, row.id)
    return refs, ObservationIndex(ctx.session, refs)


def _new_row(ctx: IngestContext, model, **values):
    row = model(**values)
    ctx.session.add(row)
    ctx.session.flush()
    return row


def season_by_year(session: Session, year: int) -> Season:
    season = session.scalar(select(Season).where(Season.year == year))
    if season is None:
        season = Season(year=year)
        session.add(season)
        session.flush()
    return season


def current_year(session: Session) -> int | None:
    return current_season_year(dict(session.execute(select(Season.year, Season.started_at)).all()))


# --- Temporadas, eventos, franquicias e identidades ----------------------------------------


def resolve_season(ctx: IngestContext, ref: ExternalRef) -> None:
    """Temporada por año oficial (RF-52): dos fuentes con el mismo año son la misma."""
    year = to_int(_own_index(ctx, ref).value("year"))
    season = season_by_year(ctx.session, year)
    _, index = _link(ctx, ref, season)
    if index.value("name") is not None:
        season.name = index.value("name")


def resolve_event(ctx: IngestContext, ref: ExternalRef) -> None:
    """Evento con el nombre tal como se publica (RF-30, RF-61)."""
    refs = refs_of_entity(ctx.session, "event", ref.entity_id)
    index = ObservationIndex(ctx.session, refs)
    event = ctx.session.get(Event, ref.entity_id)
    season = season_by_year(ctx.session, to_int(index.value("season_year")))
    if event is None:
        event = _new_row(ctx, Event, id=ref.entity_id, season_id=season.id, name=index.value("name") or "")
    event.season_id = season.id
    if index.value("name") is not None:
        event.name = index.value("name")


def resolve_franchise(ctx: IngestContext, ref: ExternalRef) -> None:
    """Franquicia (RF-10, RF-114, RF-117): su agrupación ya la decidieron los enlaces."""
    if ctx.session.get(Franchise, ref.entity_id) is None:
        _new_row(ctx, Franchise, id=ref.entity_id)


def _identity_data(identity: Identity) -> IdentityData:
    return IdentityData(
        identity.short_name, identity.abbreviation, identity.logo_url,
        identity.primary_color, identity.secondary_color,
    )


def franchise_identities(session: Session, franchise_id: uuid.UUID) -> list[IdentityVersion]:
    rows = session.scalars(select(Identity).where(Identity.franchise_id == franchise_id))
    return [IdentityVersion(i.id, _identity_data(i), i.valid_from) for i in rows]


def resolve_identity(ctx: IngestContext, ref: ExternalRef) -> None:
    """Identidad de una franquicia (RF-11, RF-73, RF-74).

    Cualquier cambio de los cinco datos crea una identidad nueva. La misma identidad
    publicada por otra fuente no se duplica: se enlaza con la vigente en esa fecha.
    """
    session = ctx.session
    index = _own_index(ctx, ref)
    franchise_id = require_entity(session, "franchise", index.value("franchise_ref"))
    data = IdentityData(
        index.value("short_name"), index.value("abbreviation"), index.value("logo_url"),
        index.value("primary_color"), index.value("secondary_color"),
    )
    current = session.get(Identity, ref.entity_id) if ref.entity_id else None
    if current is not None and current.franchise_id == franchise_id and not needs_new_identity(_identity_data(current), data):
        return

    valid_from = identity_valid_from(to_datetime(index.value("valid_from")), index.latest_seen())
    same_start = session.scalar(
        select(Identity).where(Identity.franchise_id == franchise_id, Identity.valid_from == valid_from)
    )
    in_effect = identity_at(franchise_identities(session, franchise_id), valid_from)
    if same_start is not None:
        target = same_start
        for name, value in data._asdict().items():
            setattr(target, name, value)
    elif in_effect is not None and not needs_new_identity(in_effect.data, data):
        target = session.get(Identity, in_effect.id)
    else:
        target = _new_row(ctx, Identity, franchise_id=franchise_id, valid_from=valid_from, **data._asdict())
    ref.entity_id = target.id
    session.flush()
    reresolve_placements(ctx, Placement.franchise_id == franchise_id)


# --- Jugadores y rosters -------------------------------------------------------------------


def resolve_player(ctx: IngestContext, ref: ExternalRef) -> None:
    """Jugador (RF-16, RF-17, RF-21, RF-22, RF-60, RF-77, RF-78, RF-109 a RF-111)."""
    session = ctx.session
    refs = refs_of_entity(session, "player", ref.entity_id)
    player = session.get(Player, ref.entity_id)
    if player is not None and player.personal_data_removed:
        # Los datos personales retirados no se vuelven a guardar (RF-78).
        session.execute(delete(Observation).where(
            Observation.ref_id.in_([r.id for r in refs]), Observation.field.in_(PERSONAL_FIELDS)))
    index = ObservationIndex(session, refs)
    if player is None:
        player = _new_row(ctx, Player, id=ref.entity_id, current_gamertag=index.value("gamertag"))

    player.current_gamertag = index.value("gamertag") or player.current_gamertag
    if index.has("retired"):
        player.retired = bool(index.value("retired"))

    player.real_name = index.value("real_name")
    player.country = index.value("country")
    player.birth_date = to_date(index.value("birth_date"))
    player.birth_year = to_int(index.value("birth_year"))
    player.birth_year_is_approx = False
    age = index.pick("age")
    if player.birth_date is None and player.birth_year is None and age is not None:
        player.birth_year = approx_birth_year(int(age.value), age.last_seen_at.year)
        player.birth_year_is_approx = True

    previous = [tag for tag in dict.fromkeys(index.value("previous_gamertags") or []) if tag != player.current_gamertag]
    session.execute(delete(PlayerGamertag).where(PlayerGamertag.player_id == player.id))
    for position, tag in enumerate(previous, start=1):
        session.add(PlayerGamertag(player_id=player.id, gamertag=tag, position=position))
    session.flush()


def resolve_roster(ctx: IngestContext, ref: ExternalRef) -> None:
    """Pertenencia a un roster de la temporada: solo sale de registros de roster (RF-104)."""
    session = ctx.session
    refs = refs_of_entity(session, "roster", ref.entity_id)
    index = ObservationIndex(session, refs)
    season = season_by_year(session, to_int(index.value("season_year")))
    franchise_id = require_entity(session, "franchise", index.value("franchise_ref"))
    player_id = require_entity(session, "player", index.value("player_ref"))
    roster = session.get(RosterMembership, ref.entity_id)
    if roster is None:
        roster = _new_row(ctx, RosterMembership, id=ref.entity_id, season_id=season.id,
                          player_id=player_id, franchise_id=franchise_id)
    roster.season_id, roster.player_id, roster.franchise_id = season.id, player_id, franchise_id
    roster.from_date = to_datetime(index.value("from"))
    roster.to_date = to_datetime(index.value("to"))
    session.flush()
    # La marca de suplente de sus estadísticas depende del roster (RF-103).
    reresolve_stats(ctx, PlayerMapStats.player_id == player_id)


# --- Partidos -------------------------------------------------------------------------------


def _latest_schedule(session: Session, match_id: uuid.UUID) -> MatchSchedule | None:
    return session.scalar(
        select(MatchSchedule).where(MatchSchedule.match_id == match_id).order_by(MatchSchedule.seq.desc()).limit(1)
    )


def resolve_match(ctx: IngestContext, ref: ExternalRef) -> None:
    """Partido: estado, horarios, equipos y marcadores (RF-30 a RF-39, RF-62, RF-63, RF-81 a RF-91)."""
    session = ctx.session
    refs = refs_of_entity(session, "match", ref.entity_id)
    index = ObservationIndex(session, refs)
    match = session.get(Match, ref.entity_id)
    is_new = match is None
    old_status = None if is_new else match.status

    source_status = index.value("status")
    change = (
        apply_source_status(old_status, source_status)
        if source_status is not None
        else StatusChange(status=old_status or "scheduled")
    )
    if change.cancelled:  # RF-83: el partido deja de guardarse
        if match is not None:
            # Los lados que lo tenían como origen pasan a "por definir" sin origen (RF-86).
            session.execute(update(MatchSlot).where(MatchSlot.origin_match_id == match.id)
                            .values(origin_match_id=None, origin_outcome=None))
            session.delete(match)
        for member in refs:
            member.entity_id = None
        session.flush()
        return

    event_id = require_entity(session, "event", index.value("event_ref"))
    best_of = to_int(index.value("best_of"))
    if is_new:
        if best_of is None:
            raise IngestError(f"El partido {ref.source}:{ref.source_id} no tiene formato (best_of).")
        match = _new_row(ctx, Match, id=ref.entity_id, event_id=event_id, best_of=best_of, status=change.status)
    closed = old_status == "finished"

    match.event_id = event_id
    match.status = change.status
    set_field(ctx, match, "phase", normalize_phase(index.value("phase")), closed=closed, index=index, is_new=is_new)
    if best_of is not None:
        set_field(ctx, match, "best_of", best_of, closed=closed, index=index, is_new=is_new)

    # Historial de horarios: se añade cada fecha nueva; manda la última (RF-87, RF-88).
    scheduled_at = to_datetime(index.value("scheduled_at"))
    if scheduled_at is not None:
        last = _latest_schedule(session, match.id)
        if last is None or last.scheduled_at != scheduled_at:
            session.add(MatchSchedule(match_id=match.id, scheduled_at=scheduled_at, seq=(last.seq + 1) if last else 1))

    for side in (1, 2):
        if index.has(f"slot_{side}"):
            _resolve_slot(session, match.id, side, index.value(f"slot_{side}") or {})

    if change.status in ("live", "finished"):
        maps_won = [to_int(index.value(f"maps_won_{side}")) for side in (1, 2)]
        maps_won = [v if v is None or is_valid_maps_won(v, match.best_of) else None for v in maps_won]
        if change.status == "live" and maps_won == [None, None]:
            maps_won = [0, 0]  # RF-89: en vivo sin marcador publicado
        set_field(ctx, match, "maps_won_1", maps_won[0], closed=closed, index=index, is_new=is_new)
        set_field(ctx, match, "maps_won_2", maps_won[1], closed=closed, index=index, is_new=is_new)
    else:
        match.maps_won_1 = match.maps_won_2 = None

    if change.status == "live":
        match.live_mode = index.value("live_mode")
        match.live_score_1 = to_int(index.value("live_score_1"))
        match.live_score_2 = to_int(index.value("live_score_2"))
    else:
        match.live_mode = match.live_score_1 = match.live_score_2 = None

    winner = to_int(index.value("winner_side")) if change.status == "finished" else None
    set_field(ctx, match, "winner_side", winner, closed=closed, index=index, is_new=is_new)

    if change.started and match.went_live_at is None:
        status_seen = index.pick("status")
        match.went_live_at = status_seen.last_seen_at if status_seen else index.latest_seen()
    session.flush()
    if match.went_live_at is not None:
        _start_season(ctx, match)


def _resolve_slot(session: Session, match_id: uuid.UUID, side: int, value: dict) -> None:
    """Un lado del partido: equipo, origen ("ganador/perdedor de") o nada (RF-32, RF-84, RF-86)."""
    slot = session.scalar(select(MatchSlot).where(MatchSlot.match_id == match_id, MatchSlot.side == side))
    if slot is None:
        slot = MatchSlot(match_id=match_id, side=side)
        session.add(slot)
    slot.franchise_id = slot.origin_match_id = slot.origin_outcome = None
    if value.get("franchise_ref"):
        slot.franchise_id = require_entity(session, "franchise", value["franchise_ref"])
    elif value.get("origin"):
        origin_id = entity_for(session, "match", value["origin"]["match_ref"])
        if origin_id is not None and session.get(Match, origin_id) is not None:
            slot.origin_match_id = origin_id
            slot.origin_outcome = value["origin"]["outcome"]


def _start_season(ctx: IngestContext, match: Match) -> None:
    """Fija el inicio de la temporada del partido si aún no lo tenía (RF-3, RF-53, RF-123)."""
    season = ctx.session.get(Season, ctx.session.get(Event, match.event_id).season_id)
    if season.started_at is not None:
        return
    before = current_year(ctx.session)
    season.started_at = match.went_live_at
    ctx.session.flush()
    after = current_year(ctx.session)
    if before is not None and after != before:
        ctx.pending_rollover = after


# --- Mapas y estadísticas ------------------------------------------------------------------


def resolve_match_map(ctx: IngestContext, ref: ExternalRef) -> None:
    """Mapa de un partido, identificado por partido y posición (RF-40, RF-64, RF-92, RF-95)."""
    session = ctx.session
    own = _own_index(ctx, ref)
    match_id = require_entity(session, "match", own.value("match_ref"))
    position = to_int(own.value("position"))
    if own.value("status") == "voided":  # RF-64: la versión anulada no cuenta
        ref.entity_id = None
        session.flush()
        return

    game_map = session.scalar(select(MatchMap).where(MatchMap.match_id == match_id, MatchMap.position == position))
    is_new = game_map is None
    if is_new:
        game_map = _new_row(ctx, MatchMap, match_id=match_id, position=position, played=False)
    _, index = _link(ctx, ref, game_map)
    closed = session.get(Match, match_id).status == "finished"

    game_map.played = index.value("status") == "played"
    set_field(ctx, game_map, "mode", index.value("mode"), closed=closed, index=index, is_new=is_new)
    set_field(ctx, game_map, "map_name", index.value("map_name"), closed=closed, index=index, is_new=is_new)
    for attr in ("score_1", "score_2", "winner_side"):
        value = to_int(index.value(attr)) if game_map.played else None
        set_field(ctx, game_map, attr, value, closed=closed, index=index, is_new=is_new)
    session.flush()


def mode_key(mode: str | None) -> str:
    return " ".join((mode or "").lower().replace("&", "and").split())


def _is_substitute(session: Session, match: Match, player_id: uuid.UUID, franchise_id: uuid.UUID) -> bool:
    """Suplente: jugó con un equipo a cuyo roster no pertenecía en la fecha del partido (RF-103)."""
    season_id = session.get(Event, match.event_id).season_id
    memberships = session.scalars(select(RosterMembership).where(
        RosterMembership.season_id == season_id,
        RosterMembership.player_id == player_id,
        RosterMembership.franchise_id == franchise_id,
    )).all()
    last = _latest_schedule(session, match.id)
    if last is None:
        return not memberships
    moment = last.scheduled_at
    return not any(
        (m.from_date is None or m.from_date <= moment) and (m.to_date is None or m.to_date >= moment)
        for m in memberships
    )


def resolve_player_map_stats(ctx: IngestContext, ref: ExternalRef) -> None:
    """Estadísticas de un jugador en un mapa (RF-29, RF-41 a RF-45, RF-65, RF-79, RF-95, RF-102, RF-103)."""
    session = ctx.session
    own = _own_index(ctx, ref)
    map_id = require_entity(session, "match_map", own.value("map_ref"))
    player_id = require_entity(session, "player", own.value("player_ref"))
    stats = session.scalar(select(PlayerMapStats).where(PlayerMapStats.map_id == map_id, PlayerMapStats.player_id == player_id))
    is_new = stats is None
    if is_new:
        stats = _new_row(ctx, PlayerMapStats, map_id=map_id, player_id=player_id)
    _, index = _link(ctx, ref, stats)

    game_map = session.get(MatchMap, map_id)
    match = session.get(Match, game_map.match_id)
    closed = match.status == "finished"
    relevant = COMMON_STATS + MODE_STATS.get(mode_key(game_map.mode), ())
    for attr in PLAYER_STAT_FIELDS:
        raw = index.value(attr) if attr in relevant else None
        value = to_decimal(raw) if attr == "kd" else to_int(raw)
        set_field(ctx, stats, attr, value, closed=closed, index=index, is_new=is_new)

    stats.franchise_id = require_entity(session, "franchise", index.value("franchise_ref"))
    stats.is_substitute = _is_substitute(session, match, player_id, stats.franchise_id)
    session.flush()


# --- Tabla de posiciones e historial -------------------------------------------------------


def resolve_standing(ctx: IngestContext, ref: ExternalRef) -> None:
    """Posición y puntos tal como se publican, con prioridad de la web oficial (RF-49, RF-50, RF-75, RF-122)."""
    session = ctx.session
    own = _own_index(ctx, ref)
    season = season_by_year(session, to_int(own.value("season_year")))
    franchise_id = require_entity(session, "franchise", own.value("franchise_ref"))
    standing = session.scalar(select(Standing).where(Standing.season_id == season.id, Standing.franchise_id == franchise_id))
    if standing is None:
        standing = _new_row(ctx, Standing, season_id=season.id, franchise_id=franchise_id)
    _, index = _link(ctx, ref, standing)
    standing.position = to_int(index.value("position", STANDINGS_PRIORITY))
    standing.points = to_int(index.value("points", STANDINGS_PRIORITY))
    session.flush()


def resolve_championship(ctx: IngestContext, ref: ExternalRef) -> None:
    """Campeonato mundial de un año (RF-4, RF-54, RF-55, RF-58)."""
    session = ctx.session
    year = to_int(_own_index(ctx, ref).value("year"))
    championship = session.scalar(select(Championship).where(Championship.year == year))
    is_new = championship is None
    if is_new:
        championship = _new_row(ctx, Championship, year=year)
    _, index = _link(ctx, ref, championship)
    closed = championship.completed
    for attr in ("competition", "game_name", "game_abbreviation"):
        set_field(ctx, championship, attr, index.value(attr), closed=closed, index=index, is_new=is_new)
    set_field(ctx, championship, "final_date", to_date(index.value("final_date")), closed=closed, index=index, is_new=is_new)
    if index.has("completed"):
        championship.completed = bool(index.value("completed"))
    session.flush()
    # La identidad de cada equipo depende de la fecha de la final (RF-13, RF-121, RF-124).
    reresolve_placements(ctx, Placement.championship_id == championship.id)


def resolve_placement(ctx: IngestContext, ref: ExternalRef) -> None:
    """Clasificación de un equipo en un campeonato: un premio por equipo (RF-5 a RF-9, RF-13, RF-56, RF-57, RF-59, RF-119)."""
    session = ctx.session
    own = _own_index(ctx, ref)
    championship_id = require_entity(session, "championship", own.value("championship_ref"))
    franchise_id = require_entity(session, "franchise", own.value("franchise_ref"))
    placement = session.scalar(select(Placement).where(
        Placement.championship_id == championship_id, Placement.franchise_id == franchise_id))
    is_new = placement is None
    if is_new:
        placement = _new_row(ctx, Placement, championship_id=championship_id, franchise_id=franchise_id)
    _, index = _link(ctx, ref, placement)
    championship = session.get(Championship, championship_id)
    closed = championship.completed

    place = index.value("place")
    set_field(ctx, placement, "place", place, closed=closed, index=index, is_new=is_new)
    placement.is_dq = place is not None and place.strip().upper() == "DQ"
    placement.published_team_name = index.value("published_team_name")
    set_field(ctx, placement, "prize_usd", to_decimal(index.value("prize_usd")), closed=closed, index=index, is_new=is_new)
    set_field(ctx, placement, "pool_percent", to_decimal(index.value("pool_percent")), closed=closed, index=index, is_new=is_new)

    identity = identity_for_championship(
        franchise_identities(session, franchise_id), championship.final_date,
        placement.published_team_name, championship.year,
    )
    placement.identity_id = identity.id if identity else None

    if index.has("roster"):
        session.execute(delete(PlacementRoster).where(PlacementRoster.placement_id == placement.id))
        seen = set()
        for entry in index.value("roster") or []:
            player_id = require_entity(session, "player", entry["player_ref"])
            if player_id not in seen:
                seen.add(player_id)
                session.add(PlacementRoster(placement_id=placement.id, player_id=player_id,
                                            gamertag_at_final=entry.get("gamertag_at_final")))
    session.flush()


RESOLVERS = {
    "season": resolve_season,
    "event": resolve_event,
    "franchise": resolve_franchise,
    "identity": resolve_identity,
    "player": resolve_player,
    "roster": resolve_roster,
    "match": resolve_match,
    "match_map": resolve_match_map,
    "player_map_stats": resolve_player_map_stats,
    "standing": resolve_standing,
    "championship": resolve_championship,
    "placement": resolve_placement,
}


# --- Recálculos --------------------------------------------------------------------------------


def reresolve_entity(ctx: IngestContext, kind: str, entity_id: uuid.UUID) -> None:
    """Recalcula una entidad a partir de sus observaciones, sin marcar correcciones."""
    refs = refs_of_entity(ctx.session, kind, entity_id)
    if refs:
        with corrections_off(ctx):
            RESOLVERS[kind](ctx, refs[0])


def _reresolve_rows(ctx: IngestContext, kind: str, model, condition) -> None:
    ids = ctx.session.scalars(select(model.id).where(condition)).all()
    for row_id in ids:
        reresolve_entity(ctx, kind, row_id)


def reresolve_placements(ctx: IngestContext, condition) -> None:
    _reresolve_rows(ctx, "placement", Placement, condition)


def reresolve_stats(ctx: IngestContext, condition) -> None:
    _reresolve_rows(ctx, "player_map_stats", PlayerMapStats, condition)


def reresolve_all_refs(ctx: IngestContext, kind: str) -> None:
    """Recalcula cada referencia de un tipo (tras separar jugadores, sus datos pueden cambiar de dueño)."""
    refs = ctx.session.scalars(select(ExternalRef).where(ExternalRef.kind == kind).order_by(ExternalRef.id)).all()
    with corrections_off(ctx):
        for ref in refs:
            if kind in ("roster",) and ref.entity_id is None:
                continue
            RESOLVERS[kind](ctx, ref)


# Tipos identificados por clave natural: sus filas sin ninguna referencia sobran.
NATURAL_KEY_MODELS = {"match_map": MatchMap, "player_map_stats": PlayerMapStats, "standing": Standing, "placement": Placement}


def delete_orphan_rows(session: Session) -> None:
    """Borra las filas de mapas, estadísticas, posiciones y clasificaciones que ya no tienen referencias."""
    for kind, model in NATURAL_KEY_MODELS.items():
        referenced = exists().where(ExternalRef.kind == kind, ExternalRef.entity_id == model.id)
        session.execute(delete(model).where(~referenced))
    session.flush()
