"""T-027 a T-029 · Conector de BreakingPoint, con las muestras reales recortadas de la fase F0."""

import json
from datetime import UTC, datetime

import pytest

from app.ingest.records import parse_record
from app.sources import bp
from app.sources.http import PoliteClient
from tests.unit.sources.fakes import FakeResponse, FakeTransport, SteppingClock
from tests.unit.sources.snapshots import load, next_data_html

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def records_of(kind, records):
    return [r for r in records if r["kind"] == kind]


def assert_valid(records):
    """Todo registro producido cumple el contrato de la 002."""
    for record in records:
        parse_record(record)


# --- T-027 · listado: temporadas, eventos, franquicias y partidos ------------------------------


def listing_props():
    return load("bp/matches_page.json")


def test_solo_los_eventos_de_la_cdl():
    events = listing_props()["allEvents"]
    names = [e["name"] for e in events if bp.is_cdl_event(e)]
    # La Esports World Cup (211) no es un partido oficial de la CDL (RF-53 de la 002).
    assert "Esports World Cup" not in names
    assert {"CDL Major 1 Qualifier", "CDL Major 1 Tournament", "CDL League Championship "} <= set(names)


def test_listado_produce_temporada_eventos_franquicias_e_identidades():
    records = bp.parse_listing(listing_props(), observed_at=NOW)
    assert_valid(records)
    season = records_of("season", records)[0]
    assert (season["year"], season["source_id"]) == (2026, "season:2026")
    events = records_of("event", records)
    assert {e["source_id"] for e in events} == {"100", "101", "110"}
    assert all(e["season_year"] == 2026 for e in events)
    assert next(e for e in events if e["source_id"] == "110")["name"] == "CDL League Championship"
    identity = next(r for r in records_of("identity", records) if r["franchise_ref"] == "bp:26")
    assert identity["short_name"] == "Carolina Royal Ravens"
    assert identity["abbreviation"] == "CAR"
    assert identity["primary_color"] == "#0083c1"
    assert identity["logo_url"].endswith("CAR_ROYAL_RAVENS_ALLMODE.webp")
    # Los registros llegan en orden: lo referenciado antes que lo que lo referencia (I-16 de la 002).
    kinds = [r["kind"] for r in records]
    assert kinds.index("season") < kinds.index("event") and kinds.index("franchise") < kinds.index("identity")


def test_la_temporada_y_la_proxima_si_bp_ya_la_publica():
    props = listing_props()
    props["allSeasons"] = props["allSeasons"] + [{"id": 2027, "year": 2027, "start_date": "2026-11-01", "end_date": "2027-10-01"}]
    props["allSeasons"].insert(0, {"id": 2019, "year": 2019})
    years = [r["year"] for r in records_of("season", bp.parse_listing(props, observed_at=NOW))]
    # La temporada en curso y la próxima (RF-14); nunca las anteriores (RF-1 de la 002).
    assert sorted(years) == [2026, 2027]


def test_sin_proxima_temporada_solo_la_actual_y_nunca_la_anterior():
    # Error detectado con la consulta real: BreakingPoint aún no publica la 2027 y colaba la 2025.
    props = listing_props()
    props["allSeasons"] = [{"id": 2025, "year": 2025, "start_date": "2024-11-01", "end_date": "2025-10-27"}] + props["allSeasons"]
    props["allEvents"] = props["allEvents"] + [{"id": 50, "name": "CDL Major 1 Qualifier", "season_id": 2025}]
    records = bp.parse_listing(props, observed_at=NOW)
    assert [r["year"] for r in records_of("season", records)] == [2026]
    assert "50" not in {r["source_id"] for r in records_of("event", records)}


def page_matches():
    return load("bp/trpc_matches_page.json")["data"]


def test_partidos_de_la_api_interna():
    records, seen = bp.parse_matches(page_matches(), observed_at=NOW)
    assert_valid(records)
    match = next(r for r in records if r["source_id"] == "214853")
    assert match["event_ref"] == "bp:101"
    assert match["phase"] == "grand_final"
    assert (match["best_of"], match["status"]) == (7, "finished")
    assert match["scheduled_at"] == "2026-02-01T23:00:00+00:00"
    assert match["slots"] == [{"franchise_ref": "bp:4"}, {"franchise_ref": "bp:743"}]
    assert (match["maps_won"], match["winner_side"]) == ([3, 4], 2)
    assert "bp:214853" in seen


@pytest.mark.parametrize(("side", "phase"), [
    ({"stage": "playoffs", "bracket_side": "winners"}, "winners_bracket"),
    ({"stage": "playoffs", "bracket_side": "elimination"}, "losers_bracket"),
    ({"stage": "playoffs", "bracket_side": "grand_final"}, "grand_final"),
    ({"stage": "qualifier", "bracket_side": "none"}, "week"),  # su número se calcula en la ingesta (C-13)
    ({"stage": "playoffs", "bracket_side": "none"}, None),
    (None, None),
])
def test_fase_desde_la_ronda(side, phase):
    assert bp.phase_of(side) == phase


@pytest.mark.parametrize(("status", "expected"), [
    ("complete", "finished"), ("live", "live"), ("upcoming", "scheduled"), ("cancelled", "cancelled"),
])
def test_estados_conocidos(status, expected):
    assert bp.status_of(status) == expected


def test_un_estado_desconocido_se_marca_como_ilegible_sin_perder_el_partido():
    raw = dict(page_matches()[0], status="suspended_by_aliens")
    records, _ = bp.parse_matches([raw], observed_at=NOW)
    match = records_of("match", records)[0]
    assert "status" not in match and match["unreadable"] == ["status"]
    assert_valid(records)


def test_origen_del_bracket_para_el_equipo_aun_por_decidir():
    source = dict(page_matches()[0], id=1, winner_next_match_id=2, winner_next_match_team_position=2,
                  loser_next_match_id=None)
    target = dict(page_matches()[0], id=2, team_1_id=4, team_2_id=None, status="upcoming",
                  team_1_score=None, team_2_score=None, winner_id=None)
    records, _ = bp.parse_matches([source, target], observed_at=NOW)
    match = next(r for r in records if r["source_id"] == "2")
    assert match["slots"] == [{"franchise_ref": "bp:4"}, {"origin": {"match_ref": "bp:1", "outcome": "winner"}}]
    # Un partido programado no publica marcador.
    assert "maps_won" not in match and "winner_side" not in match
    # El partido de origen va antes que el que lo referencia.
    ids = [r["source_id"] for r in records if r["kind"] == "match"]
    assert ids.index("1") < ids.index("2")


# --- T-028 · detalle de partido ------------------------------------------------------------


def test_detalle_con_mapas_y_estadisticas():
    records = bp.parse_match_detail(load("bp/match_detail.json"), observed_at=NOW)
    assert_valid(records)
    maps = records_of("match_map", records)
    assert [m["position"] for m in maps] == [1, 2, 3]
    first = maps[0]
    assert (first["source_id"], first["match_ref"]) == ("214853/1", "bp:214853")
    assert (first["mode"], first["map_name"], first["status"]) == ("Hardpoint", "Colossus", "played")
    assert (first["score"], first["winner_side"]) == ([158, 250], 2)
    stats = records_of("player_map_stats", records)
    assert all(s["source_id"].count("/") == 2 and s["source_id"].startswith("214853/") for s in stats)


def test_estadisticas_por_modo_y_ausencia_distinta_de_cero():
    records = bp.parse_match_detail(load("bp/match_detail.json"), observed_at=NOW)
    stats = records_of("player_map_stats", records)
    hp = next(s for s in stats if s["map_ref"] == "bp:214853/1")
    assert hp["hill_time"] == 19 and hp["contested_hill_time"] == 0 and "kd" not in hp
    snd = next(s for s in stats if s["map_ref"] == "bp:214853/2")
    assert "hill_time" not in snd  # no publicada: ausente, nunca 0
    assert snd["first_bloods"] == 0 and "first_deaths" in snd
    # Cada jugador que aparece en las estadísticas llega antes como registro de jugador.
    players = {r["source_id"] for r in records_of("player", records)}
    assert {s["player_ref"].split(":", 1)[1] for s in stats} <= players
    kinds = [r["kind"] for r in records]
    assert kinds.index("player") < kinds.index("player_map_stats")


def test_mapas_no_jugados_desde_los_mapas_previstos_de_la_serie():
    records = bp.parse_match_detail(load("bp/match_series_maps.json"), observed_at=NOW)
    maps = records_of("match_map", records)
    assert [(m["position"], m["status"]) for m in maps] == [(1, "played"), (2, "played"), (3, "played"),
                                                            (4, "not_played"), (5, "not_played")]
    fourth, fifth = maps[3], maps[4]
    # Nombres y modos a partir de los identificadores de mapa y modo de los mapas jugados.
    assert (fourth["mode"], fourth["map_name"]) == ("Hardpoint", "Colossus")
    assert (fifth["mode"], fifth["map_name"]) == ("Search & Destroy", "Den")
    assert "score" not in fourth
    assert_valid(records)


def test_un_mapa_previsto_con_identificador_desconocido_queda_sin_nombre():
    page = load("bp/match_series_maps.json")
    query = page["trpcState"]["json"]["queries"][0]
    query["state"]["data"].append({"map_id": 999, "map_number": 6, "mode_id": 999})
    maps = records_of("match_map", bp.parse_match_detail(page, observed_at=NOW))
    sixth = maps[-1]
    assert sixth["position"] == 6 and "map_name" not in sixth and "mode" not in sixth


# --- T-029 · equipos y jugadores ------------------------------------------------------------


def test_ficha_de_jugador():
    content = load("bp/player_page.json")
    records = bp.parse_player_page(content, season=(2026, "2025-10-28", "2026-10-29"), observed_at=NOW)
    assert_valid(records)
    player = records_of("player", records)[0]
    assert (player["gamertag"], player["real_name"]) == ("Shotzzy", "Anthony Cuevas-Castro")
    assert player["birth_date"] == "2001-07-04" and player["retired"] is False
    # El país llega como número: se traduce con la tabla de países de la curación (I-6, T-093).
    assert player["country"] == "bp:234"
    roster = records_of("roster", records)
    assert len(roster) == 1 and roster[0]["franchise_ref"] == "bp:4" and roster[0]["season_year"] == 2026


def test_un_jugador_retirado_no_entra_en_el_roster():
    content = load("bp/player_page.json")
    content["player"] = dict(content["player"], retired=True)
    records = bp.parse_player_page(content, season=(2026, "2025-10-28", "2026-10-29"), observed_at=NOW)
    assert records_of("roster", records) == []


def test_tabla_desde_la_ficha_de_equipo():
    team = {"team": {"id": 4, "name": "OpTic Texas"}, "standings": {"rank": 1, "points": 575, "season_id": 2026}}
    records = bp.parse_team_page(team, observed_at=NOW)
    assert_valid(records)
    standing = records_of("standing", records)[0]
    assert (standing["season_year"], standing["franchise_ref"], standing["position"], standing["points"]) == (2026, "bp:4", 1, 575)


# --- Extracción de la página y consultas ---------------------------------------------------


def test_extrae_el_json_incrustado():
    assert bp.extract_next_data(next_data_html({"a": 1})) == {"props": {"pageProps": {"a": 1}}}


def test_una_pagina_sin_json_incrustado_es_formato_no_entendido():
    with pytest.raises(bp.UnreadableResponse):
        bp.extract_next_data("<html>Cambió todo</html>")


def test_consulta_de_la_api_interna_paginada_con_identificacion():
    clock = SteppingClock()
    page1 = {"result": {"data": {"json": {"data": page_matches()[:1], "nextCursor": 5}}}}
    page2 = {"result": {"data": {"json": {"data": page_matches()[1:], "nextCursor": None}}}}
    url = f"{bp.BASE_URL}/api/trpc/cached.matches.fetchMatchesPage"
    transport = FakeTransport({f"{bp.BASE_URL}/robots.txt": FakeResponse(404),
                               url: [FakeResponse(200, json.dumps(page1)), FakeResponse(200, json.dumps(page2))]}, clock)
    client = PoliteClient("bp", transport, clock=clock, sleep=clock.sleep, base_url=bp.BASE_URL)
    matches = bp.fetch_matches(client, season_year=2026, event_ids=[101])
    assert [m["id"] for m in matches] == [m["id"] for m in page_matches()]
    second_input = json.loads(transport.calls[-1]["params"]["input"])["json"]
    assert second_input["cursor"] == 5 and second_input["eventIds"] == [101] and second_input["cdlOnly"] is True


def test_consulta_regular_con_respuesta_vacia_cuenta_los_elementos():
    clock = SteppingClock()
    listing = listing_props()
    empty = {"result": {"data": {"json": {"data": [], "nextCursor": None}}}}
    events = {"result": {"data": {"json": [101]}}}
    transport = FakeTransport({
        f"{bp.BASE_URL}/robots.txt": FakeResponse(404),
        f"{bp.BASE_URL}/matches": FakeResponse(200, next_data_html(listing)),
        f"{bp.BASE_URL}/api/trpc/matches.fetchEventIdsWithCompletedMatches": FakeResponse(200, json.dumps(events)),
        f"{bp.BASE_URL}/api/trpc/cached.matches.fetchMatchesPage": FakeResponse(200, json.dumps(empty)),
    }, clock)
    client = PoliteClient("bp", transport, clock=clock, sleep=clock.sleep, base_url=bp.BASE_URL)
    result = bp.consult_regular(client, observed_at=NOW)
    assert result.outcome == "success" and result.item_count == 0
    assert result.job == "regular" and result.source == "bp"


def test_la_anterior_sigue_mientras_la_nueva_no_tiene_partidos_jugados():
    # RF-2 de la 002: hasta que un partido de la nueva pase a en vivo, la actual es la anterior.
    props = listing_props()
    props["allSeasons"] = props["allSeasons"] + [{"id": 2027, "year": 2027, "start_date": "2026-09-01", "end_date": "2027-10-01"}]
    by_date = [r["year"] for r in records_of("season", bp.parse_listing(props, observed_at=NOW))]
    assert by_date == [2027]
    with_previous = [r["year"] for r in records_of("season", bp.parse_listing(props, observed_at=NOW, include_previous=True))]
    assert with_previous == [2026, 2027]


def test_consulta_regular_incluye_la_anterior_si_la_nueva_aun_no_ha_jugado():
    from app.sources.simulated import simulated_transport
    clock = SteppingClock(datetime(2026, 12, 4, 12, 0, tzinfo=UTC))
    transport = simulated_transport("cambio_de_temporada", clock, app_env="development")
    client = PoliteClient("bp", transport, clock=clock, sleep=clock.sleep, base_url=bp.BASE_URL)
    result = bp.consult_regular(client, observed_at=clock.now())
    assert sorted(r["year"] for r in records_of("season", result.records)) == [2026, 2027]
