"""Fuente simulada para desarrollo y pruebas (plan de la spec 003, §6.4; T-035).

Responde como BreakingPoint y la Wiki a partir de **escenarios**: respuestas que cambian con el
tiempo simulado (segundos desde el inicio del escenario). Con ella se comprueban a mano y en las
pruebas los casos que la spec pide simular (criterio 4 de su §6), sin salir a internet (RF-10).

Nunca funciona en producción (RF-9): `simulated_transport` se niega con `APP_ENV=production`.

Los escenarios se definen con ayudantes que reproducen la estructura real de las respuestas
(la de las muestras de la fase F0), en lugar de archivos JSON escritos a mano (plan I-14).
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlsplit

from app.sources import bp

DAY = 24 * 3600
# Hora de inicio de los escenarios: una hora antes de los partidos (`T`), dentro de la ventana
# previa. `retake sync` en modo simulado arranca su reloj aquí (plan I-32).
SCENARIO_START = datetime(2026, 12, 5, 19, 0, tzinfo=UTC)


class ScenarioNotAllowed(Exception):
    """La fuente simulada no se admite en este entorno (producción)."""


@dataclass(frozen=True)
class Stub:
    """Respuesta simulada de una dirección durante un intervalo `[start, end)` de segundos.

    `match` restringe la respuesta a peticiones cuyos parámetros contengan esos valores; en la API
    interna de BreakingPoint se comparan con el JSON de `input`.
    """

    url: str
    body: str = ""
    status: int = 200
    start: float = 0
    end: float | None = None
    match: dict = field(default_factory=dict)


@dataclass
class SimResponse:
    status_code: int
    text: str

    @property
    def content(self) -> bytes:
        return self.text.encode("utf-8")


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    stubs: tuple[Stub, ...]


class SimulatedTransport:
    """Transporte que responde con los `Stub` vigentes en el segundo simulado de cada petición."""

    def __init__(self, scenario: Scenario, clock):
        self.scenario = scenario
        self._clock = clock
        self._started_at = clock.now()

    def elapsed(self) -> float:
        return (self._clock.now() - self._started_at).total_seconds()

    @staticmethod
    def _params_of(params: dict | None) -> dict:
        params = dict(params or {})
        if "input" in params:
            try:
                params.update(json.loads(params["input"]).get("json") or {})
            except (ValueError, AttributeError):
                pass
        return params

    def __call__(self, url, params=None, headers=None, timeout=None) -> SimResponse:
        now, given = self.elapsed(), self._params_of(params)
        candidates = [
            s for s in self.scenario.stubs
            if s.url == url and s.start <= now and (s.end is None or now < s.end)
            and all(given.get(k) == v for k, v in s.match.items())
        ]
        if not candidates:
            return SimResponse(404, "Not Found (fuente simulada)")
        stub = candidates[-1]  # el más específico o el último definido
        return SimResponse(stub.status, stub.body)


def simulated_transport(name: str, clock, app_env: str) -> SimulatedTransport:
    """Transporte de un escenario. Nunca en producción (RF-9).

    Raises:
        ScenarioNotAllowed: con `APP_ENV=production`.
        KeyError: si el escenario no existe.
    """
    if app_env == "production":
        raise ScenarioNotAllowed("La fuente simulada no se usa nunca en producción.")
    return SimulatedTransport(SCENARIOS[name](), clock)


# --- Ayudantes con la estructura real de las respuestas ----------------------------------------

BP_MATCHES = f"{bp.BASE_URL}/matches"
BP_API_PAGE = f"{bp.BASE_URL}/api/trpc/cached.matches.fetchMatchesPage"

TEAMS = [
    {"id": 4, "name": "[FICTICIO] OpTic Texas", "name_short": "TX", "color_hex": "#93C852",
     "logo_darkmode": "https://dfpiiufxcciujugzjvgx.supabase.co/storage/v1/object/public/teams/TX.webp"},
    {"id": 743, "name": "[FICTICIO] Paris Gentle Mates", "name_short": "PGM", "color_hex": "#E6007E"},
    {"id": 26, "name": "[FICTICIO] Carolina Royal Ravens", "name_short": "CAR", "color_hex": "#0083c1"},
    {"id": 14, "name": "[FICTICIO] Boston Breach", "name_short": "BOS", "color_hex": "#02FF5B"},
]
SEASON_2026 = {"id": 2026, "year": 2026, "start_date": "2025-10-28", "end_date": "2026-10-29"}
SEASON_2027 = {"id": 2027, "year": 2027, "start_date": "2026-10-30", "end_date": "2027-10-29"}
EVENTS_2026 = [{"id": 100, "name": "CDL Major 1 Qualifier", "season_id": 2026},
               {"id": 101, "name": "CDL Major 1 Tournament", "season_id": 2026}]
EVENT_2027 = {"id": 300, "name": "CDL Major 1 Qualifier", "season_id": 2027}


def _page(props: dict) -> str:
    return f'<script id="__NEXT_DATA__" type="application/json">{json.dumps({"props": {"pageProps": props}})}</script>'


def _trpc(data) -> str:
    return json.dumps({"result": {"data": {"json": data}}})


def _match(match_id: int, status: str, datetime_: str, score=(0, 0), winner=None, event_id=100, teams=(4, 743),
           best_of=5, round_=None) -> dict:
    return {"id": match_id, "event_id": event_id, "datetime": datetime_, "best_of": best_of, "status": status,
            "team_1_id": teams[0], "team_2_id": teams[1], "team_1_score": score[0], "team_2_score": score[1],
            "winner_id": winner, "round": round_ or {"name": "Major Qualifier", "stage": "qualifier", "bracket_side": "none"}}


def _game(num: int, mode: str, map_name: str, score, winner, teams=(4, 743)) -> dict:
    ids = {"Hardpoint": 1, "Search & Destroy": 2, "Overload": 5}
    return {"game_num": num, "map_id": 60 + num, "mode_id": ids[mode], "maps": {"name": map_name}, "modes": {"name": mode},
            "team_1_id": teams[0], "team_2_id": teams[1], "team_1_score": score[0], "team_2_score": score[1],
            "winner_id": winner,
            "player_stats": [{"player_id": 9001, "player_tag": "[FICTICIO] Uno", "team_id": teams[0], "kills": 20, "deaths": 18},
                             {"player_id": 9002, "player_tag": "[FICTICIO] Dos", "team_id": teams[1], "kills": 17, "deaths": 21}]}


def _listing(seasons=(SEASON_2026,), events=tuple(EVENTS_2026), start=0, end=None) -> Stub:
    return Stub(BP_MATCHES, _page({"allSeasons": list(seasons), "allTeams": TEAMS, "allEvents": list(events)}), start=start, end=end)


def _api_page(matches: list[dict], status: str, start=0, end=None) -> Stub:
    return Stub(BP_API_PAGE, _trpc({"data": matches, "nextCursor": None}), start=start, end=end, match={"status": status})


def _detail(match: dict, games: list[dict], start=0, end=None, bans=None) -> Stub:
    props = {"initialMatchState": {**match, "games": games},
             "trpcState": {"json": {"queries": [{"queryKey": [["matches", "fetchGameBans"], {}], "state": {"data": bans or []}}]}}}
    return Stub(f"{bp.BASE_URL}/match/{match['id']}", _page(props), start=start, end=end)


# Mapas de una serie, en orden, y el marcador de un mapa ganado en cada modo.
MAP_POOL = (("Hardpoint", "Colossus"), ("Search & Destroy", "Raid"), ("Overload", "Den"),
            ("Hardpoint", "Exposure"), ("Search & Destroy", "Raid"))
MAP_SCORES = {"Hardpoint": (250, 200), "Search & Destroy": (6, 3), "Overload": (3, 1)}


def _series(match: dict, start=0, end=None) -> Stub:
    """Página de un partido cuyos mapas cuadran con su marcador: los ganados y, en vivo, el que se juega.

    El trabajador consulta la página de cada partido en vivo o terminado (RF-16, RF-19); sin ella,
    el recorrido manual en modo simulado registraría un 404 en cada revisión (T-057).
    """
    t1, t2 = match["team_1_id"], match["team_2_id"]
    s1, s2 = match["team_1_score"] or 0, match["team_2_score"] or 0
    # El ganador de la serie gana el último mapa.
    winners = [t2] * s2 + [t1] * s1 if match["winner_id"] == t1 else [t1] * s1 + [t2] * s2
    games = []
    for num, winner in enumerate(winners, start=1):
        mode, map_name = MAP_POOL[num - 1]
        high, low = MAP_SCORES[mode]
        games.append(_game(num, mode, map_name, (high, low) if winner == t1 else (low, high), winner, teams=(t1, t2)))
    if match["status"] == "live":
        mode, map_name = MAP_POOL[len(games)]
        games.append(_game(len(games) + 1, mode, map_name, (0, 0), None, teams=(t1, t2)))
    return _detail(match, games, start, end)


# Un jugador ficticio por equipo, con el mismo identificador que en las estadísticas de `_game`.
PLAYERS = {4: 9001, 743: 9002, 26: 9003, 14: 9004}


def _team_pages() -> tuple[Stub, ...]:
    """Fichas de equipo (puesto y puntos) y de sus jugadores (datos y roster) para el "Resto" (RF-18)."""
    stubs = []
    for rank, team in enumerate(TEAMS, start=1):
        player_id = PLAYERS[team["id"]]
        stubs.append(Stub(f"{bp.BASE_URL}/teams/{team['id']}", _page({
            "team": {"id": team["id"], "players": [{"id": player_id, "retired": False, "current_team_id": team["id"]}]},
            "standings": {"season_id": 2026, "rank": rank, "points": 100 - 10 * rank},
        })))
        stubs.append(Stub(f"{bp.BASE_URL}/players/{player_id}", _page({
            "player": {"id": player_id, "tag": f"[FICTICIO] Jugador {player_id}", "first_name": "[FICTICIO]",
                       "last_name": f"Nombre {player_id}", "date_of_birth": "2000-01-01",
                       "retired": False},
            "teamHistory": [{"team_id": team["id"], "role_name": "Player", "start_date": "2025-10-01", "end_date": None}],
        })))
    return tuple(stubs)


def _robots() -> tuple[Stub, ...]:
    """Normas para robots (sin publicar) y fichas de equipo y jugador, comunes a todos los escenarios."""
    return (Stub(f"{bp.BASE_URL}/robots.txt", status=404),) + _team_pages()


# --- Escenarios del plan §6.4 ------------------------------------------------------------------

T = "2026-12-05T20:00:00+00:00"


def partido_en_vivo() -> Scenario:
    """Un partido programado empieza al minuto, cambia de marcador y termina 3-1 a los 5 minutos."""
    scheduled = _match(900, "upcoming", T, score=(None, None))
    live_1 = _match(900, "live", T, score=(0, 0))
    live_2 = _match(900, "live", T, score=(1, 0))
    final = _match(900, "complete", T, score=(3, 1), winner=4)
    return Scenario("partido_en_vivo", partido_en_vivo.__doc__, _robots() + (
        _listing(),
        _api_page([scheduled], "upcoming_live", 0, 60), _api_page([], "completed", 0, 300),
        _api_page([live_1], "upcoming_live", 60, 180), _api_page([live_2], "upcoming_live", 180, 300),
        _api_page([], "upcoming_live", 300), _api_page([final], "completed", 300),
        _detail(live_1, [_game(1, "Hardpoint", "Colossus", (120, 90), None)], 60, 180),
        _detail(live_2, [_game(1, "Hardpoint", "Colossus", (250, 180), 4), _game(2, "Search & Destroy", "Raid", (2, 1), None)], 180, 300),
        _detail(final, [_game(1, "Hardpoint", "Colossus", (250, 180), 4), _game(2, "Search & Destroy", "Raid", (6, 3), 4),
                        _game(3, "Overload", "Den", (2, 4), 743), _game(4, "Hardpoint", "Exposure", (250, 201), 4)], 300,
                bans=[{"map_id": 61, "map_number": 1, "mode_id": 1}, {"map_id": 65, "map_number": 5, "mode_id": 2}]),
    ))


def marcador_que_retrocede() -> Scenario:
    """En vivo, la fuente publica 2-1 y al minuto, por error, 1-1; después 2-2 (RF-59)."""
    stages = [(_match(901, "live", T, score=(2, 1)), 0, 60), (_match(901, "live", T, score=(1, 1)), 60, 120),
              (_match(901, "live", T, score=(2, 2)), 120, None)]
    return Scenario("marcador_que_retrocede", marcador_que_retrocede.__doc__, _robots() + (
        _listing(), _api_page([], "completed"),
        *(_api_page([match], "upcoming_live", start, end) for match, start, end in stages),
        *(_series(match, start, end) for match, start, end in stages),
    ))


def fuente_caida() -> Scenario:
    """BreakingPoint responde 503 durante 2 minutos y después vuelve (RF-43 a RF-45)."""
    down = (Stub(BP_MATCHES, "<h1>503 Service Unavailable</h1>", status=503, start=0, end=120),
            Stub(BP_API_PAGE, "Service Unavailable", status=503, start=0, end=120))
    final = _match(902, "complete", T, (3, 0), 4)
    up = (_listing(start=120), _api_page([final], "completed", 120), _api_page([], "upcoming_live", 120),
          _series(final, start=120))
    return Scenario("fuente_caida", fuente_caida.__doc__, _robots() + down + up)


def respuesta_vacia() -> Scenario:
    """La lista de partidos terminados trae dos partidos y al minuto llega vacía (RF-46)."""
    matches = [_match(903, "complete", T, (3, 2), 4), _match(904, "complete", T, (1, 3), 743)]
    return Scenario("respuesta_vacia", respuesta_vacia.__doc__, _robots() + (
        _listing(), _api_page([], "upcoming_live"),
        _api_page(matches, "completed", 0, 60), _api_page([], "completed", 60),
        *(_series(m) for m in matches),  # las páginas siguen ahí aunque la lista llegue vacía
    ))


def dato_ilegible() -> Scenario:
    """Un partido con un estado desconocido (RF-47, RF-48). El premio ilegible del historial se prueba
    con la importación de los archivos de la Wiki (I-26)."""
    return Scenario("dato_ilegible", dato_ilegible.__doc__, _robots() + (
        _listing(), _api_page([], "upcoming_live"),
        _api_page([_match(905, "suspended_by_aliens", T, (1, 1))], "completed"),
    ))


def partido_desaparece() -> Scenario:
    """Un partido terminado deja de aparecer 25 horas y después reaparece (RF-50 a RF-52)."""
    match = _match(906, "complete", T, (3, 1), 4)
    return Scenario("partido_desaparece", partido_desaparece.__doc__, _robots() + (
        _listing(), _api_page([], "upcoming_live"),
        _api_page([match], "completed", 0, 60), _api_page([], "completed", 60, 60 + 25 * 3600),
        _api_page([match], "completed", 60 + 25 * 3600),
        # Mientras falta, tampoco responde su página: si respondiera, seguiría apareciendo (RF-50).
        _series(match, 0, 60), _series(match, 60 + 25 * 3600),
    ))


def varios_en_vivo() -> Scenario:
    """Tres partidos en vivo a la vez, que empezaron a distintas horas (RF-23 a RF-26)."""
    live = [_match(907, "live", "2026-12-05T20:00:00+00:00", (1, 0), teams=(4, 743)),
            _match(908, "live", "2026-12-05T19:30:00+00:00", (0, 1), teams=(26, 14)),
            _match(909, "live", "2026-12-05T20:30:00+00:00", (0, 0), teams=(743, 26))]
    return Scenario("varios_en_vivo", varios_en_vivo.__doc__, _robots() + (
        _listing(), _api_page([], "completed"), _api_page(live, "upcoming_live"),
        *(_detail(m, [_game(1, "Hardpoint", "Colossus", (100, 90), None, teams=(m["team_1_id"], m["team_2_id"]))]) for m in live),
    ))


def cambio_de_temporada() -> Scenario:
    """BreakingPoint publica la temporada 2027 con un partido programado; a la hora empieza (RF-3, RF-14, RF-15)."""
    first = {**_match(910, "upcoming", "2026-12-04T20:00:00+00:00", (None, None), event_id=300)}
    live = {**_match(910, "live", "2026-12-04T20:00:00+00:00", (0, 0), event_id=300)}
    return Scenario("cambio_de_temporada", cambio_de_temporada.__doc__, _robots() + (
        _listing(seasons=(SEASON_2026, SEASON_2027), events=(*EVENTS_2026, EVENT_2027)),
        _api_page([], "completed"),
        _api_page([first], "upcoming_live", 0, 3600), _api_page([live], "upcoming_live", 3600),
        _series(live, start=3600),
    ))


# Equipos que no están en la lista de la temporada (RF-18a, C-22): una franquicia que la fuente ya
# lista con otro número (está en la tabla) y un equipo de fuera de la CDL (no lo está).
UNLISTED_FRANCHISE = {"id": 6, "name": "[FICTICIO] Boston Breach", "name_short": "BOS", "color_hex": "#02FF5B",
                      "start_date": "2021-12-15"}
OUTSIDER_TEAM = {"id": 744, "name": "[FICTICIO] Huntsmen", "name_short": "HUNT", "color_hex": "#235330",
                 "start_date": "2025-11-01"}
GUEST_PLAYER = 9010


def _unlisted_team_page(team: dict, standing: dict | None = None, players: tuple[int, ...] = ()) -> Stub:
    members = [{"id": pid, "retired": False, "current_team_id": team["id"]} for pid in players]
    return Stub(f"{bp.BASE_URL}/teams/{team['id']}", _page({"team": {**team, "players": members}, "standings": standing}))


def _guest_player_page() -> Stub:
    """Jugador de un equipo invitado, con los mismos datos que uno de la CDL (RF-117b de la 002)."""
    return Stub(f"{bp.BASE_URL}/players/{GUEST_PLAYER}", _page({
        "player": {"id": GUEST_PLAYER, "tag": "[FICTICIO] Invitado", "first_name": "[FICTICIO]", "last_name": "Invitado",
                   "date_of_birth": "2004-05-06", "retired": False},
        "teamHistory": [{"team_id": OUTSIDER_TEAM["id"], "role_name": "Player", "start_date": "2025-11-01", "end_date": None}],
    }))


def franquicia_sin_listar() -> Scenario:
    """Partidos con equipos que no están en la lista de la temporada (RF-18a, RF-18b; C-22, C-24): una
    franquicia renombrada con otro número, que está en la tabla; un equipo invitado, que no lo está; y
    un equipo cuya ficha no responde."""
    renamed = _match(911, "complete", T, (3, 1), 4, teams=(4, 6))
    outsider = _match(912, "complete", T, (3, 0), 743, teams=(743, 744))
    missing = _match(914, "complete", T, (3, 2), 26, teams=(26, 745))
    upcoming = _match(913, "upcoming", "2026-12-06T20:00:00+00:00", (None, None), teams=(6, 26))
    return Scenario("franquicia_sin_listar", franquicia_sin_listar.__doc__, _robots() + (
        _listing(), _api_page([renamed, outsider, missing], "completed"), _api_page([upcoming], "upcoming_live"),
        _unlisted_team_page(UNLISTED_FRANCHISE, {"season_id": 2026, "rank": 5, "points": 50}),
        _unlisted_team_page(OUTSIDER_TEAM, players=(GUEST_PLAYER,)), _guest_player_page(),
        _series(renamed), _series(outsider), _series(missing),
    ))


SCENARIOS: dict[str, Callable[[], Scenario]] = {
    fn.__name__: fn for fn in (partido_en_vivo, marcador_que_retrocede, fuente_caida, respuesta_vacia, dato_ilegible,
                               partido_desaparece, varios_en_vivo, cambio_de_temporada, franquicia_sin_listar)
}


def hosts() -> set[str]:
    """Servidores que responde la fuente simulada."""
    return {urlsplit(s.url).netloc for build in SCENARIOS.values() for s in build().stubs}
