"""Conector de BreakingPoint.gg (plan de la spec 003, §2.2; mapa de datos de la fase F0).

BreakingPoint es la fuente de toda la temporada actual (plan I-3):

- **API interna JSON** (tRPC) que usa su propia web: `cached.matches.fetchMatchesPage`, paginada.
- **JSON incrustado** (`__NEXT_DATA__`) de sus páginas: `/matches` (temporadas, eventos y
  equipos), `/match/{id}` (mapas, estadísticas y mapas previstos de la serie), `/teams/{id}`
  (tabla) y `/players/{id}` (datos personales e historial de equipos).

Las funciones `parse_*` son puras: traducen lo que publica BreakingPoint a registros de fuente
(contrato de la 002) sin tocar la red, y se prueban con las muestras reales de la fase F0.
Lo que no entienden no lo inventan: lo marcan como ilegible (plan D-8).
"""

import json
import re
from collections.abc import Iterable, Sequence
from datetime import date, datetime

from app.sources.contract import ConsultaResult, Rejection, UnreadableResponse
from app.sources.http import Forbidden, PoliteClient, SourceUnavailable

__all__ = ["UnreadableResponse"]

SOURCE = "bp"
BASE_URL = "https://breakingpoint.gg"

# Estado de BreakingPoint → estado de la fuente del contrato de la 002 (plan §3.4 de la 002).
STATUS_MAP = {
    "complete": "finished", "completed": "finished", "finished": "finished",
    "live": "live", "in_progress": "live", "ongoing": "live",
    "upcoming": "scheduled", "scheduled": "scheduled", "not_started": "scheduled",
    "postponed": "postponed", "forfeit": "forfeit",
    "cancelled": "cancelled", "canceled": "cancelled",
}

# Lado del bracket de una ronda → fase de la 002 (RF-31). La semana de los clasificatorios no la
# publica BreakingPoint: la calcula la ingesta (C-13, T-092).
BRACKET_PHASES = {"winners": "winners_bracket", "elimination": "losers_bracket", "losers": "losers_bracket",
                  "grand_final": "grand_final"}

# Estadística de BreakingPoint → estadística de la 002 (RF-41 a RF-44). El K/D no lo publica (C-12).
STAT_MAP = {
    "kills": "kills", "deaths": "deaths", "damage": "damage", "assists": "assists",
    "hill_time": "hill_time", "contested_hill_time": "contested_hill_time",
    "first_blood_count": "first_bloods", "first_death_count": "first_deaths",
    "plant_count": "plants", "defuse_count": "defuses",
    "zone_capture_count": "zone_captures", "overloads": "overloads",
}

_NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


# --- Utilidades ---------------------------------------------------------------------------------


def _ref(source_id: object) -> str:
    return f"{SOURCE}:{source_id}"


def _record(kind: str, source_id: object, observed_at: datetime, **fields) -> dict:
    """Registro de fuente sin los campos nulos: un campo omitido no borra nada (D-8 de la 002)."""
    record = {"kind": kind, "source": SOURCE, "source_id": str(source_id), "observed_at": observed_at.isoformat()}
    record.update({name: value for name, value in fields.items() if value is not None})
    return record


def _day_start(value: str | None) -> str | None:
    """Fecha `AAAA-MM-DD` → instante a las 00:00 UTC de ese día."""
    return f"{value}T00:00:00+00:00" if value else None


def extract_next_data(html: str) -> dict:
    """JSON incrustado de una página de Next.js.

    Raises:
        UnreadableResponse: si la página no lo trae o no es JSON (cambio de formato).
    """
    match = _NEXT_DATA.search(html)
    if not match:
        raise UnreadableResponse("la página no trae el JSON incrustado (__NEXT_DATA__)")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise UnreadableResponse(f"JSON incrustado no válido: {error}") from None


def trpc_query(page_props: dict, procedure: str) -> object:
    """Datos de una consulta tRPC ya resuelta dentro del JSON incrustado de una página, o `None`."""
    for query in (page_props.get("trpcState") or {}).get("json", {}).get("queries", []):
        key = query.get("queryKey") or []
        path = key[0] if key else []
        if isinstance(path, list) and ".".join(path).endswith(procedure):
            return (query.get("state") or {}).get("data")
    return None


def is_cdl_event(event: dict) -> bool:
    """Evento de la CDL: su nombre empieza por "CDL".

    El filtro `cdlOnly` de BreakingPoint incluye también la Esports World Cup, que no es un
    partido oficial de la CDL (RF-53 de la 002).
    """
    return str(event.get("name") or "").strip().startswith("CDL ")


def phase_of(round_: dict | None) -> str | None:
    """Fase de un partido a partir de su ronda; `None` si no es ninguna de las cinco fases.

    Un partido de clasificatorio es de fase `week`; BreakingPoint no publica su número de
    semana, que se calcula en la ingesta (C-13).
    """
    if not round_:
        return None
    if str(round_.get("stage") or "").lower() == "qualifier":
        return "week"
    return BRACKET_PHASES.get(str(round_.get("bracket_side") or "").lower())


def status_of(status: object) -> str | None:
    """Estado de la fuente, o `None` si BreakingPoint publica uno desconocido."""
    return STATUS_MAP.get(str(status or "").lower())


# --- T-027 · listado: temporadas, eventos, franquicias e identidades ----------------------------


def recent_seasons(page_props: dict, today: date, include_previous: bool = False) -> list[dict]:
    """La temporada en curso por fechas y las posteriores que ya publique BreakingPoint (RF-14).

    - En curso por fechas = la más reciente cuya fecha de inicio ya ha llegado; si ninguna trae
      fecha, la más reciente. Las anteriores no interesan (RF-1 de la 002)…
    - …salvo `include_previous`: mientras la temporada en curso por fechas no haya jugado ningún
      partido, la actual sigue siendo la anterior (RF-2 de la 002) y también se incluye.
    """
    seasons = sorted((s for s in page_props.get("allSeasons") or [] if isinstance(s.get("year"), int)),
                     key=lambda s: s["year"])
    if not seasons:
        return []
    started = [i for i, s in enumerate(seasons) if s.get("start_date") and date.fromisoformat(s["start_date"]) <= today]
    current = started[-1] if started else len(seasons) - 1
    first = max(current - 1, 0) if include_previous else current
    return seasons[first:]


def parse_listing(page_props: dict, observed_at: datetime, include_previous: bool = False) -> list[dict]:
    """Temporadas, eventos de la CDL, franquicias e identidades de la página `/matches`."""
    records: list[dict] = []
    seasons = recent_seasons(page_props, observed_at.date(), include_previous)
    years = {s["year"] for s in seasons}
    for season in seasons:
        records.append(_record("season", f"season:{season['year']}", observed_at,
                               year=season["year"], name=f"CDL {season['year']}"))
    for event in page_props.get("allEvents") or []:
        if event.get("season_id") in years and is_cdl_event(event):
            records.append(_record("event", event["id"], observed_at,
                                   season_year=event["season_id"], name=str(event["name"]).strip()))
    for team in page_props.get("allTeams") or []:
        records.append(_record("franchise", team["id"], observed_at))
        records.append(_record(
            "identity", f"{team['id']}#identity", observed_at,
            franchise_ref=_ref(team["id"]),
            short_name=team.get("name"),
            abbreviation=team.get("name_short"),
            # La web de Retake es solo de tema oscuro (RF-5 de la 001): el logo para fondo oscuro.
            logo_url=team.get("logo_darkmode") or team.get("logo_main"),
            primary_color=team.get("color_hex"),
        ))
    return records


# --- T-027 · partidos de la API interna -------------------------------------------------------


def _origins(matches: Sequence[dict]) -> dict[tuple[object, int], dict]:
    """Origen de cada lado aún por decidir: BreakingPoint publica en el partido de origen a qué
    partido y posición pasa su ganador o su perdedor (RF-84 de la 002)."""
    origins: dict[tuple[object, int], dict] = {}
    for match in matches:
        for outcome in ("winner", "loser"):
            target = match.get(f"{outcome}_next_match_id")
            position = match.get(f"{outcome}_next_match_team_position")
            if target is not None and position in (1, 2):
                origins[(target, position)] = {"match_ref": _ref(match["id"]), "outcome": outcome}
    return origins


def _slot(team_id: object, origin: dict | None) -> dict:
    if team_id is not None:
        return {"franchise_ref": _ref(team_id)}
    if origin is not None:
        return {"origin": origin}
    return {}  # se sabe que aún no hay equipo ni origen publicado (RF-86 de la 002)


def _dependency_order(matches: Sequence[dict], origins: dict) -> list[dict]:
    """Partidos de origen antes que los que los referencian (I-16 de la 002)."""
    by_id = {m["id"]: m for m in matches}
    depth: dict[object, int] = {}

    def depth_of(match_id: object, seen: frozenset = frozenset()) -> int:
        if match_id in depth:
            return depth[match_id]
        sources = [o["match_ref"].split(":", 1)[1] for (target, _), o in origins.items() if target == match_id]
        value = 0
        for source_id in sources:
            key = next((k for k in by_id if str(k) == source_id), None)
            if key is not None and key not in seen:
                value = max(value, depth_of(key, seen | {match_id}) + 1)
        depth[match_id] = value
        return value

    return sorted(matches, key=lambda m: (depth_of(m["id"]), m.get("datetime") or "", str(m["id"])))


def parse_matches(matches: Iterable[dict], observed_at: datetime) -> tuple[list[dict], list[str]]:
    """Partidos de la API interna (`fetchMatchesPage`).

    Returns:
        Los registros de partido y las referencias vistas (para las desapariciones, RF-50).
    """
    matches = list(matches)
    origins = _origins(matches)
    records, seen = [], []
    for match in _dependency_order(matches, origins):
        status = status_of(match.get("status"))
        unreadable = [] if status is not None else ["status"]
        scored = status in ("live", "finished")
        scores = (match.get("team_1_score"), match.get("team_2_score"))
        winner = match.get("winner_id")
        winner_side = None
        if status == "finished" and winner is not None:
            winner_side = 1 if winner == match.get("team_1_id") else 2 if winner == match.get("team_2_id") else None
        records.append(_record(
            "match", match["id"], observed_at,
            event_ref=_ref(match["event_id"]),
            phase=phase_of(match.get("round")),
            best_of=match.get("best_of"),
            status=status,
            scheduled_at=match.get("datetime"),
            slots=[_slot(match.get("team_1_id"), origins.get((match["id"], 1))),
                   _slot(match.get("team_2_id"), origins.get((match["id"], 2)))],
            maps_won=list(scores) if scored and None not in scores else None,
            winner_side=winner_side,
            unreadable=unreadable or None,
        ))
        seen.append(_ref(match["id"]))
    return records, seen


# --- T-028 · detalle de partido ----------------------------------------------------------------


def _name(obj: object) -> str | None:
    return obj.get("name") if isinstance(obj, dict) else None


def parse_match_detail(page_props: dict, observed_at: datetime) -> list[dict]:
    """Detalle de un partido (`/match/{id}`): estado, marcador, mapas, estadísticas y no jugados.

    - Un mapa sin ganador es el mapa en curso: no es un mapa jugado (glosario de la 002) y su
      marcador va en `live_map` del partido.
    - Los mapas previstos que no llegaron a jugarse (`fetchGameBans`) solo se registran con el
      partido finalizado (RF-92 de la 002).
    """
    state = page_props.get("initialMatchState") or {}
    match_id = state["id"]
    games = sorted(state.get("games") or [], key=lambda g: g.get("game_num") or 0)
    maps = {g.get("map_id"): _name(g.get("maps")) for g in games}
    modes = {g.get("mode_id"): _name(g.get("modes")) for g in games}
    status = status_of(state.get("status"))

    in_progress = next((g for g in games if g.get("winner_id") is None), None)
    live_map = None
    if status == "live" and in_progress is not None:
        live_map = {"mode": _name(in_progress.get("modes")),
                    "score": [in_progress.get("team_1_score"), in_progress.get("team_2_score")]}

    team_1, team_2 = state.get("team_1_id"), state.get("team_2_id")
    side = lambda winner: 1 if winner == team_1 else 2 if winner == team_2 else None  # noqa: E731
    scores = (state.get("team_1_score"), state.get("team_2_score"))
    records = [_record(
        "match", match_id, observed_at,
        event_ref=_ref(state["event_id"]) if state.get("event_id") is not None else None,
        best_of=state.get("best_of"),
        status=status,
        maps_won=list(scores) if status in ("live", "finished") and None not in scores else None,
        live_map=live_map,
        winner_side=side(state.get("winner_id")) if status == "finished" else None,
        unreadable=None if status is not None else ["status"],
    )]

    players: dict[object, str] = {}
    map_records, stat_records = [], []
    for game in games:
        if game.get("winner_id") is None:
            continue
        position = game.get("game_num")
        map_id = f"{match_id}/{position}"
        map_records.append(_record(
            "match_map", map_id, observed_at, match_ref=_ref(match_id), position=position,
            mode=_name(game.get("modes")), map_name=_name(game.get("maps")), status="played",
            score=[game.get("team_1_score"), game.get("team_2_score")], winner_side=side(game.get("winner_id")),
        ))
        for stats in game.get("player_stats") or []:
            player_id = stats.get("player_id")
            if player_id is None:
                continue
            players.setdefault(player_id, stats.get("player_tag"))
            stat_records.append(_record(
                "player_map_stats", f"{map_id}/{player_id}", observed_at,
                map_ref=_ref(map_id), player_ref=_ref(player_id), franchise_ref=_ref(stats.get("team_id")),
                **{ours: stats.get(theirs) for theirs, ours in STAT_MAP.items()},
            ))

    if status == "finished":
        played = {g.get("game_num") for g in games if g.get("winner_id") is not None}
        for planned in trpc_query(page_props, "fetchGameBans") or []:
            number = planned.get("map_number")
            if isinstance(number, int) and number > 0 and number not in played:
                map_records.append(_record(
                    "match_map", f"{match_id}/{number}", observed_at, match_ref=_ref(match_id), position=number,
                    mode=modes.get(planned.get("mode_id")), map_name=maps.get(planned.get("map_id")), status="not_played",
                ))

    player_records = [_record("player", pid, observed_at, gamertag=tag) for pid, tag in players.items() if tag]
    map_records.sort(key=lambda r: r["position"])
    return records + player_records + map_records + stat_records


# --- T-029 · equipos y jugadores ---------------------------------------------------------------


def parse_team_page(page_props: dict, observed_at: datetime) -> list[dict]:
    """Puesto y puntos de la temporada en la ficha de equipo (tabla de posiciones)."""
    team, standing = page_props.get("team") or {}, page_props.get("standings") or {}
    if not team.get("id") or not standing.get("season_id"):
        return []
    season = standing["season_id"]
    return [_record("standing", f"{season}/standings/{team['id']}", observed_at, season_year=season,
                    franchise_ref=_ref(team["id"]), position=standing.get("rank"), points=standing.get("points"))]


def team_player_ids(page_props: dict) -> list[object]:
    """Jugadores en activo del equipo (la ficha incluye también a retirados del mismo equipo)."""
    team = page_props.get("team") or {}
    return [p["id"] for p in team.get("players") or [] if not p.get("retired") and p.get("current_team_id") == team.get("id")]


def _overlaps(start: str | None, end: str | None, season_start: str, season_end: str) -> bool:
    start_d = date.fromisoformat(start) if start else date.min
    end_d = date.fromisoformat(end) if end else date.max
    return start_d <= date.fromisoformat(season_end) and end_d >= date.fromisoformat(season_start)


def parse_player_page(page_props: dict, season: tuple[int, str, str], observed_at: datetime) -> list[dict]:
    """Ficha de jugador (`/players/{id}`): datos personales publicados y roster de la temporada.

    - El país solo llega como número: se registra como `bp:<número>` y la ingesta lo traduce con
      la tabla de países de la curación (plan I-6, T-093).
    - El roster sale del historial de equipos que se solapa con la temporada; un jugador retirado
      no entra en ningún roster.

    Args:
        season: Año, fecha de inicio y fecha de fin de la temporada (de `allSeasons`).
    """
    player = page_props.get("player") or {}
    player_id = player.get("id")
    if player_id is None or not player.get("tag"):
        return []
    year, season_start, season_end = season
    real_name = " ".join(part for part in (player.get("first_name"), player.get("last_name")) if part) or None
    country = player.get("country_id")
    records = [_record(
        "player", player_id, observed_at, gamertag=player["tag"], real_name=real_name,
        country=f"bp:{country}" if country is not None else None,
        birth_date=player.get("date_of_birth"), retired=player.get("retired"),
    )]
    if player.get("retired"):
        return records
    for entry in page_props.get("teamHistory") or []:
        if entry.get("role_name") not in (None, "Player"):
            continue  # entrenadores y personal técnico no forman parte del roster
        if not _overlaps(entry.get("start_date"), entry.get("end_date"), season_start, season_end):
            continue
        records.append(_record(
            "roster", f"{year}/{entry['team_id']}/{player_id}", observed_at, season_year=year,
            franchise_ref=_ref(entry["team_id"]), player_ref=_ref(player_id),
            **{"from": _day_start(entry.get("start_date")), "to": _day_start(entry.get("end_date"))},
        ))
    return records


# --- Consultas a la red ------------------------------------------------------------------------


def fetch_page_props(client: PoliteClient, path: str) -> dict:
    """`pageProps` del JSON incrustado de una página de BreakingPoint."""
    return extract_next_data(client.get(f"{BASE_URL}{path}").text).get("props", {}).get("pageProps", {})


def trpc(client: PoliteClient, procedure: str, payload: dict) -> object:
    """Llama a un procedimiento de la API interna y devuelve sus datos.

    Raises:
        UnreadableResponse: si la respuesta no tiene la forma esperada.
    """
    response = client.get(f"{BASE_URL}/api/trpc/{procedure}", params={"input": json.dumps({"json": payload})})
    try:
        return json.loads(response.text)["result"]["data"]["json"]
    except (ValueError, KeyError, TypeError) as error:
        raise UnreadableResponse(f"respuesta de {procedure} no entendida: {error}") from None


def fetch_matches(client: PoliteClient, season_year: int, event_ids: Sequence[int], status: str = "completed") -> list[dict]:
    """Todos los partidos de los eventos indicados, siguiendo la paginación (`nextCursor`)."""
    matches, cursor = [], None
    while True:
        payload = {"seasonId": season_year, "status": status, "cdlOnly": True, "teamIds": [], "eventIds": list(event_ids),
                   "pageSize": 100, "slug": "cod", "direction": "forward"}
        if cursor is not None:
            payload["cursor"] = cursor
        page = trpc(client, "cached.matches.fetchMatchesPage", payload)
        if not isinstance(page, dict) or not isinstance(page.get("data"), list):
            raise UnreadableResponse("fetchMatchesPage sin lista de partidos")
        matches.extend(page["data"])
        cursor = page.get("nextCursor")
        if cursor is None:
            return matches


def _failure(job: str, error: Exception) -> ConsultaResult:
    outcome = "forbidden" if isinstance(error, Forbidden) else "failure"
    return ConsultaResult(source=SOURCE, job=job, outcome=outcome, message=str(error))


def _events_by_season(records: list[dict]) -> dict[int, list[int]]:
    by_season: dict[int, list[int]] = {}
    for record in records:
        if record["kind"] == "event":
            by_season.setdefault(record["season_year"], []).append(int(record["source_id"]))
    return by_season


def _current_season(page_props: dict, year: int | None) -> tuple[int, str, str] | None:
    """Año, inicio y fin de la temporada actual según `allSeasons` (para las fichas de jugador)."""
    for season in page_props.get("allSeasons") or []:
        if season.get("year") == year and season.get("start_date") and season.get("end_date"):
            return year, season["start_date"], season["end_date"]
    return None


def _listing_and_matches(client: PoliteClient, observed_at: datetime, statuses: tuple[str, ...]):
    """Listado de `/matches` y partidos de los eventos de la CDL con los estados indicados.

    Si la temporada en curso por fechas aún no ha jugado ningún partido, se incluye también la
    anterior, que sigue siendo la actual (RF-2 de la 002).
    """
    props = fetch_page_props(client, "/matches")
    records = parse_listing(props, observed_at)
    by_season = _events_by_season(records)

    def season_matches(year: int, ids: list[int]) -> list[dict]:
        return [m for status in statuses for m in fetch_matches(client, year, ids, status)] if ids else []

    raw = [m for year, ids in sorted(by_season.items()) for m in season_matches(year, ids)]
    current_year = min(by_season, default=None)
    played = any(status_of(m.get("status")) in ("live", "finished") and
                 any(m.get("event_id") == e for e in by_season.get(current_year, [])) for m in raw)
    if current_year is not None and not played and "completed" in statuses:
        records = parse_listing(props, observed_at, include_previous=True)
        previous = {y: ids for y, ids in _events_by_season(records).items() if y not in by_season}
        raw += [m for year, ids in sorted(previous.items()) for m in season_matches(year, ids)]
        current_year = min(previous, default=current_year)
    return props, records, raw, current_year


def consult_regular(client: PoliteClient, observed_at: datetime, job: str = "regular") -> ConsultaResult:
    """Listado de temporadas, eventos y equipos, y todos los partidos de los eventos de la CDL.

    Devuelve también los equipos y las fechas de la temporada actual, para que el "Resto" siga
    con sus fichas de equipo y de jugador (plan §5, RF-18).
    """
    try:
        props, records, raw, current_year = _listing_and_matches(client, observed_at, ("completed", "upcoming_live"))
        match_records, seen = parse_matches(raw, observed_at)
    except (Forbidden, SourceUnavailable, UnreadableResponse) as error:
        return _failure(job, error)
    teams = tuple(r["source_id"] for r in records if r["kind"] == "franchise")
    return ConsultaResult(source=SOURCE, job=job, outcome="success", records=records + match_records, seen=seen,
                          item_count=len(raw), teams=teams, season=_current_season(props, current_year))


def consult_upcoming(client: PoliteClient, observed_at: datetime, job: str) -> ConsultaResult:
    """Solo la lista de partidos próximos y en vivo (plan §5: "Antes del partido" y "En vivo").

    Es más ligera que el listado completo: no pide los partidos terminados. Su número de elementos
    puede llegar a 0 sin que sea un fallo (la temporada acaba).
    """
    try:
        _, records, raw, _ = _listing_and_matches(client, observed_at, ("upcoming_live",))
        match_records, seen = parse_matches(raw, observed_at)
    except (Forbidden, SourceUnavailable, UnreadableResponse) as error:
        return _failure(job, error)
    return ConsultaResult(source=SOURCE, job=job, outcome="success", records=records + match_records, seen=seen,
                          item_count=len(raw))


def consult_match(client: PoliteClient, match_id: object, observed_at: datetime, job: str) -> ConsultaResult:
    """Detalle de un partido: en vivo, antes del partido o revisión de un partido terminado."""
    try:
        records = parse_match_detail(fetch_page_props(client, f"/match/{match_id}"), observed_at)
    except (Forbidden, SourceUnavailable, UnreadableResponse, KeyError) as error:
        return _failure(job, error)
    return ConsultaResult(source=SOURCE, job=job, outcome="success", records=records, seen=[_ref(match_id)], item_count=1)


def consult_teams(client: PoliteClient, team_ids: Sequence[object], season: tuple[int, str, str],
                  observed_at: datetime, job: str = "regular") -> ConsultaResult:
    """Fichas de equipo (tabla) y de sus jugadores en activo (datos personales y rosters)."""
    records: list[dict] = []
    rejected: list[Rejection] = []
    try:
        for team_id in team_ids:
            team_props = fetch_page_props(client, f"/teams/{team_id}")
            records.extend(parse_team_page(team_props, observed_at))
            for player_id in team_player_ids(team_props):
                try:
                    records.extend(parse_player_page(fetch_page_props(client, f"/players/{player_id}"), season, observed_at))
                except UnreadableResponse as error:
                    rejected.append(Rejection(ref=_ref(player_id), field="player", reason=str(error)))
    except (Forbidden, SourceUnavailable, UnreadableResponse) as error:
        return _failure(job, error)
    return ConsultaResult(source=SOURCE, job=job, outcome="success", records=records, rejected=rejected,
                          item_count=None).with_rejections_outcome()  # no es un listado completo (RF-46)
