"""Esquemas de respuesta de la API (plan de la spec 002, §2.3).

- Nombres de campo en `camelCase` y fechas ISO 8601 en UTC.
- Un valor nulo significa "no se sabe" o "no publicado"; nunca se rellena con 0 (RF-65).
- Nunca se devuelve la fecha ni el año de nacimiento de un jugador (RF-24, plan D-10).
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SeasonOut(ApiModel):
    year: int
    name: str | None
    started_at: datetime


class IdentityOut(ApiModel):
    id: str
    short_name: str
    abbreviation: str | None
    logo_url: str | None
    primary_color: str | None
    secondary_color: str | None
    valid_from: datetime


class FranchiseOut(ApiModel):
    id: str
    identities: list[IdentityOut]


class AgeOut(ApiModel):
    """Edad en años cumplidos en UTC: `min == max` si es exacta (RF-23, RF-108)."""

    min: int
    max: int


class PlayerOut(ApiModel):
    id: str
    current_gamertag: str
    previous_gamertags: list[str]
    real_name: str | None
    country: str | None
    age: AgeOut | None
    role: Literal["SMG", "AR"] | None
    team_franchise_id: str | None
    is_current_season: bool
    is_free_agent: bool
    championship_ids: list[str]


class EventOut(ApiModel):
    id: str
    name: str
    season_year: int


class OriginOut(ApiModel):
    match_id: str
    outcome: Literal["winner", "loser"]


class SlotOut(ApiModel):
    franchise_id: str | None
    identity: IdentityOut | None
    origin: OriginOut | None


class LiveMapOut(ApiModel):
    mode: str | None
    score: list[int | None] | None


class StatsOut(ApiModel):
    player_id: str
    franchise_id: str | None
    is_substitute: bool
    kills: int | None
    deaths: int | None
    kd: float | None
    damage: int | None
    assists: int | None
    hill_time: int | None
    contested_hill_time: int | None
    first_bloods: int | None
    first_deaths: int | None
    plants: int | None
    defuses: int | None
    zone_captures: int | None
    overloads: int | None
    corrected_fields: list[str]


class MatchMapOut(ApiModel):
    position: int
    mode: str | None
    map_name: str | None
    played: bool
    score: list[int | None] | None
    winner_side: int | None
    corrected_fields: list[str]
    stats: list[StatsOut]


class MatchOut(ApiModel):
    id: str
    event_id: str
    event_name: str
    phase: str | None
    best_of: int
    status: Literal["scheduled", "live", "finished"]
    scheduled_at: datetime | None
    schedule_history: list[datetime]
    slots: list[SlotOut]
    maps_won: list[int | None] | None
    live_map: LiveMapOut | None
    winner_side: int | None
    corrected_fields: list[str]
    maps: list[MatchMapOut]


class StandingOut(ApiModel):
    franchise_id: str
    identity: IdentityOut | None
    position: int | None
    points: int | None


class RosterEntryOut(ApiModel):
    player_id: str
    gamertag_at_final: str | None
    current_gamertag: str


class PlacementOut(ApiModel):
    franchise_id: str
    identity: IdentityOut | None
    place: str | None
    is_dq: bool
    prize_usd: float | None
    pool_percent: float | None
    roster: list[RosterEntryOut]
    corrected_fields: list[str]


class ChampionshipOut(ApiModel):
    id: str
    year: int
    competition: str | None
    game_name: str | None
    game_abbreviation: str | None
    final_date: date | None
    placements: list[PlacementOut]
