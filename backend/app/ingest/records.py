"""Registros de fuente: el contrato de entrada del backend (plan de la spec 002, §2.1 y D-3).

La spec 003 traducirá cada fuente a estos registros; hasta entonces salen de los datos
de prueba. Aquí solo se comprueba la **forma** de cada registro. Los valores concretos
(negativos, logos, fases…) se validan después, campo a campo, para que un valor
imposible descarte solo ese dato y no el registro entero (RF-100).

Los textos se conservan tal cual, sin recortar ni interpretar (RF-129).
"""

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from app.domain.vocabulary import SOURCES

Source = Literal["bp", "wiki", "cdl"]
assert set(Source.__args__) == set(SOURCES)

# Estados que puede publicar una fuente (plan §3.4).
SourceStatus = Literal["scheduled", "postponed", "live", "finished", "forfeit", "cancelled"]

# Valor que se valida campo a campo en la ingesta (números, marcadores, K/D…).
Loose = Any


class RecordError(ValueError):
    """El registro no tiene la forma del contrato; el mensaje explica por qué."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class RefKey(_Strict):
    """Referencia externa: un objeto tal como lo identifica una fuente.

    Se puede escribir como objeto (`{"source": "bp", "source_id": "123"}`) o como
    texto `"bp:123"`; todo lo que va tras el primer `:` es el identificador.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Source
    source_id: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _from_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            source, separator, source_id = value.partition(":")
            if not separator:
                raise ValueError('una referencia en texto debe tener la forma "fuente:identificador"')
            return {"source": source, "source_id": source_id}
        return value

    def __str__(self) -> str:
        return f"{self.source}:{self.source_id}"


# Campos comunes que nunca pueden marcarse como ilegibles.
_COMMON_FIELDS = {"kind", "source", "source_id", "observed_at", "same_as", "fictional", "unreadable"}


class _Record(_Strict):
    """Campos comunes a todos los registros (plan §2.1).

    `unreadable` (spec 003, plan §3.2) lista los campos que la fuente publica pero el
    conector no ha podido entender: la ingesta los trata como no publicados por esa fuente
    y cede el turno a las demás (RF-48, RF-49).
    """

    source: Source
    source_id: str = Field(min_length=1)
    observed_at: AwareDatetime
    same_as: list[RefKey] = Field(default_factory=list)
    fictional: bool = False
    unreadable: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unreadable_are_own_fields(self):
        own = set(type(self).model_fields) - _COMMON_FIELDS
        unknown = [name for name in self.unreadable if name not in own]
        if unknown:
            raise ValueError(f"unreadable solo admite campos propios del registro; no: {unknown}")
        return self

    @property
    def key(self) -> RefKey:
        return RefKey(source=self.source, source_id=self.source_id)


class SeasonRecord(_Record):
    kind: Literal["season"]
    year: int
    name: str | None = None


class EventRecord(_Record):
    kind: Literal["event"]
    season_year: int
    name: str | None = None


class FranchiseRecord(_Record):
    kind: Literal["franchise"]
    predecessor: RefKey | None = None
    guest: bool | None = None  # equipo invitado (RF-117a; C-23 de la 003); sin valor, la fuente no lo dice


class IdentityRecord(_Record):
    kind: Literal["identity"]
    franchise_ref: RefKey
    short_name: str = Field(min_length=1)
    abbreviation: str | None = None
    logo_url: Loose = None
    primary_color: str | None = None
    secondary_color: str | None = None
    valid_from: AwareDatetime | None = None


class PlayerRecord(_Record):
    kind: Literal["player"]
    gamertag: str = Field(min_length=1)
    previous_gamertags: list[str] | None = None
    real_name: str | None = None
    country: str | None = None
    birth_date: date | None = None
    birth_year: int | None = None
    age: int | None = None
    retired: bool | None = None


class RosterRecord(_Record):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    kind: Literal["roster"]
    season_year: int
    franchise_ref: RefKey
    player_ref: RefKey
    from_: AwareDatetime | None = Field(default=None, alias="from")
    to: AwareDatetime | None = None


class Origin(_Strict):
    """Origen de un equipo aún por decidir: ganador o perdedor de otro partido (RF-84)."""

    match_ref: RefKey
    outcome: Literal["winner", "loser"]


class Slot(_Strict):
    """Un lado de un partido: equipo conocido, origen o ninguno de los dos (RF-32, RF-84, RF-86)."""

    franchise_ref: RefKey | None = None
    origin: Origin | None = None

    @model_validator(mode="after")
    def _team_or_origin(self) -> "Slot":
        if self.franchise_ref is not None and self.origin is not None:
            raise ValueError("un lado no puede tener equipo y origen a la vez")
        return self


class LiveMap(_Strict):
    mode: str | None = None
    score: tuple[Loose, Loose] | None = None


class MatchRecord(_Record):
    kind: Literal["match"]
    event_ref: RefKey
    phase: str | None = None
    week: Loose = None  # spec 003 (C-13): número de semana, si la fuente lo publica
    best_of: Loose = None
    status: SourceStatus | None = None
    scheduled_at: AwareDatetime | None = None
    slots: tuple[Slot | None, Slot | None] | None = None
    maps_won: tuple[Loose, Loose] | None = None
    live_map: LiveMap | None = None
    winner_side: Loose = None


class MatchMapRecord(_Record):
    kind: Literal["match_map"]
    match_ref: RefKey
    position: int = Field(gt=0)
    mode: str | None = None
    map_name: str | None = None
    status: Literal["played", "not_played", "voided"]
    score: tuple[Loose, Loose] | None = None
    winner_side: Loose = None


class PlayerMapStatsRecord(_Record):
    kind: Literal["player_map_stats"]
    map_ref: RefKey
    player_ref: RefKey
    franchise_ref: RefKey
    kills: Loose = None
    deaths: Loose = None
    kd: Loose = None
    damage: Loose = None
    assists: Loose = None
    hill_time: Loose = None
    contested_hill_time: Loose = None
    first_bloods: Loose = None
    first_deaths: Loose = None
    plants: Loose = None
    defuses: Loose = None
    zone_captures: Loose = None
    overloads: Loose = None


class StandingRecord(_Record):
    kind: Literal["standing"]
    season_year: int
    franchise_ref: RefKey
    position: Loose = None
    points: Loose = None


class ChampionshipRecord(_Record):
    kind: Literal["championship"]
    year: int
    competition: str | None = None
    game_name: str | None = None
    game_abbreviation: str | None = None
    final_date: date | None = None
    completed: bool | None = None


class RosterEntry(_Strict):
    player_ref: RefKey
    gamertag_at_final: str | None = None


class PlacementRecord(_Record):
    kind: Literal["placement"]
    championship_ref: RefKey
    franchise_ref: RefKey
    published_team_name: str | None = None
    place: str | None = None
    prize_usd: Loose = None
    pool_percent: Loose = None
    roster: list[RosterEntry] | None = None


SourceRecord = Annotated[
    SeasonRecord
    | EventRecord
    | FranchiseRecord
    | IdentityRecord
    | PlayerRecord
    | RosterRecord
    | MatchRecord
    | MatchMapRecord
    | PlayerMapStatsRecord
    | StandingRecord
    | ChampionshipRecord
    | PlacementRecord,
    Field(discriminator="kind"),
]

_ADAPTER = TypeAdapter(SourceRecord)


def parse_record(raw: object):
    """Convierte un registro en bruto (p. ej. leído de JSON) en su modelo.

    Raises:
        RecordError: si el registro no tiene la forma del contrato.
    """
    try:
        return _ADAPTER.validate_python(raw)
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc']) or 'registro'}: {issue['msg']}"
            for issue in error.errors()
        )
        raise RecordError(f"Registro mal formado: {problems}") from None
