"""Campos que aporta cada tipo de registro y su validación (RF-100, RF-101, RF-130).

Cada función devuelve una lista `(campo, valor, es_válido)` solo con los campos que el
registro trae: un campo omitido no genera observación y, por tanto, no borra un
valor anterior (plan D-8).
"""

from sqlalchemy.orm import Session

from app.db.models import Match
from app.db.models.matches import PLAYER_STAT_FIELDS
from app.domain.validation import (
    is_valid_logo_url,
    is_valid_maps_won,
    is_valid_non_negative,
    is_valid_pool_percent,
)
from app.ingest import records as r
from app.ingest.store import entity_for

Field = tuple[str, object, bool]


def _valid_side(value: object) -> bool:
    return value in (1, 2) and not isinstance(value, bool)


def _valid_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _present(pairs: list[tuple[str, object, bool]]) -> list[Field]:
    return [(name, value, valid) for name, value, valid in pairs if value is not None]


def _plain(record, *names: str) -> list[Field]:
    """Campos de texto o fecha que siempre son válidos si vienen."""
    return _present([(name, getattr(record, name), True) for name in names])


def season_fields(record: r.SeasonRecord, session: Session) -> list[Field]:
    return _plain(record, "year", "name")


def event_fields(record: r.EventRecord, session: Session) -> list[Field]:
    return _plain(record, "season_year", "name")


def franchise_fields(record: r.FranchiseRecord, session: Session) -> list[Field]:
    return []  # la predecesora es un enlace, no un campo


def identity_fields(record: r.IdentityRecord, session: Session) -> list[Field]:
    return _present([
        ("franchise_ref", record.franchise_ref, True),
        ("short_name", record.short_name, True),
        ("abbreviation", record.abbreviation, True),
        ("logo_url", record.logo_url, is_valid_logo_url(record.logo_url)),
        ("primary_color", record.primary_color, True),
        ("secondary_color", record.secondary_color, True),
        ("valid_from", record.valid_from, True),
    ])


def player_fields(record: r.PlayerRecord, session: Session) -> list[Field]:
    return _present([
        ("gamertag", record.gamertag, True),
        ("previous_gamertags", record.previous_gamertags, True),
        ("real_name", record.real_name, True),
        ("country", record.country, True),
        ("birth_date", record.birth_date, True),
        ("birth_year", record.birth_year, True),
        ("age", record.age, record.age is not None and record.age >= 0),
        ("retired", record.retired, True),
    ])


def roster_fields(record: r.RosterRecord, session: Session) -> list[Field]:
    return _present([
        ("season_year", record.season_year, True),
        ("franchise_ref", record.franchise_ref, True),
        ("player_ref", record.player_ref, True),
        ("from", record.from_, True),
        ("to", record.to, True),
    ])


def _slot_value(slot: r.Slot | None) -> dict:
    """Un lado vacío se guarda como `{}`: "se sabe que aún no hay equipo ni origen"."""
    return {} if slot is None else slot.model_dump(mode="json", exclude_none=True)


def match_fields(record: r.MatchRecord, session: Session) -> list[Field]:
    best_of = record.best_of if _valid_positive_int(record.best_of) else None
    if best_of is None:
        # Para validar los mapas ganados sirve el formato ya guardado.
        entity = entity_for(session, "match", record.key)
        stored = session.get(Match, entity) if entity else None
        best_of = stored.best_of if stored else None

    def maps_won_valid(value: object) -> bool:
        return is_valid_maps_won(value, best_of) if best_of else is_valid_non_negative(value)

    pairs = [
        ("event_ref", record.event_ref, True),
        ("phase", record.phase, True),
        ("week", record.week, _valid_positive_int(record.week)),
        ("best_of", record.best_of, _valid_positive_int(record.best_of)),
        ("status", record.status, True),
        ("scheduled_at", record.scheduled_at, True),
        ("winner_side", record.winner_side, _valid_side(record.winner_side)),
    ]
    if record.slots is not None:
        pairs += [("slot_1", _slot_value(record.slots[0]), True), ("slot_2", _slot_value(record.slots[1]), True)]
    if record.maps_won is not None:
        pairs += [(f"maps_won_{i + 1}", v, maps_won_valid(v)) for i, v in enumerate(record.maps_won)]
    if record.live_map is not None:
        pairs.append(("live_mode", record.live_map.mode, True))
        if record.live_map.score is not None:
            pairs += [(f"live_score_{i + 1}", v, is_valid_non_negative(v)) for i, v in enumerate(record.live_map.score)]
    return _present(pairs)


def match_map_fields(record: r.MatchMapRecord, session: Session) -> list[Field]:
    pairs = [
        ("match_ref", record.match_ref, True),
        ("position", record.position, True),
        ("mode", record.mode, True),
        ("map_name", record.map_name, True),
        ("status", record.status, True),
        ("winner_side", record.winner_side, _valid_side(record.winner_side)),
    ]
    if record.score is not None:
        pairs += [(f"score_{i + 1}", v, is_valid_non_negative(v)) for i, v in enumerate(record.score)]
    return _present(pairs)


def player_map_stats_fields(record: r.PlayerMapStatsRecord, session: Session) -> list[Field]:
    pairs = [
        ("map_ref", record.map_ref, True),
        ("player_ref", record.player_ref, True),
        ("franchise_ref", record.franchise_ref, True),
    ]
    pairs += [(name, getattr(record, name), is_valid_non_negative(getattr(record, name))) for name in PLAYER_STAT_FIELDS]
    return _present(pairs)


def standing_fields(record: r.StandingRecord, session: Session) -> list[Field]:
    return _present([
        ("season_year", record.season_year, True),
        ("franchise_ref", record.franchise_ref, True),
        ("position", record.position, _valid_positive_int(record.position)),
        ("points", record.points, is_valid_non_negative(record.points)),
    ])


def championship_fields(record: r.ChampionshipRecord, session: Session) -> list[Field]:
    return _plain(record, "year", "competition", "game_name", "game_abbreviation", "final_date", "completed")


def placement_fields(record: r.PlacementRecord, session: Session) -> list[Field]:
    roster = None if record.roster is None else [e.model_dump(mode="json") for e in record.roster]
    return _present([
        ("championship_ref", record.championship_ref, True),
        ("franchise_ref", record.franchise_ref, True),
        ("published_team_name", record.published_team_name, True),
        ("place", record.place, True),
        ("prize_usd", record.prize_usd, is_valid_non_negative(record.prize_usd)),
        ("pool_percent", record.pool_percent, is_valid_pool_percent(record.pool_percent)),
        ("roster", roster, True),
    ])


FIELD_EXTRACTORS = {
    "season": season_fields,
    "event": event_fields,
    "franchise": franchise_fields,
    "identity": identity_fields,
    "player": player_fields,
    "roster": roster_fields,
    "match": match_fields,
    "match_map": match_map_fields,
    "player_map_stats": player_map_stats_fields,
    "standing": standing_fields,
    "championship": championship_fields,
    "placement": placement_fields,
}
