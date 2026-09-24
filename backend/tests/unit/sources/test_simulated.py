"""T-035 · Fuente simulada: escenarios reproducibles, nunca en producción."""

from datetime import UTC, datetime

import pytest

from app.sources import bp
from app.sources.http import PoliteClient
from app.sources.simulated import SCENARIOS, ScenarioNotAllowed, simulated_transport
from tests.unit.sources.fakes import SteppingClock

START = datetime(2026, 12, 5, 19, 0, tzinfo=UTC)
CHECKPOINTS = [0, 30, 61, 121, 181, 301, 3601, 2 * 86400 + 1, 26 * 3600]


def client_for(name):
    clock = SteppingClock(START)
    transport = simulated_transport(name, clock, app_env="development")
    return PoliteClient("bp", transport, clock=clock, sleep=clock.sleep, base_url=bp.BASE_URL), transport, clock


def replay(name):
    """Pide cada dirección del escenario en cada instante de control y devuelve lo recibido."""
    clock = SteppingClock(START)
    transport = simulated_transport(name, clock, app_env="development")
    seen = []
    for second in CHECKPOINTS:
        clock.advance(START.timestamp() + second - clock.instant.timestamp())
        for stub in transport.scenario.stubs:
            params = {"input": '{"json": ' + str(stub.match).replace("'", '"') + "}"} if stub.match else None
            response = transport(stub.url, params=params)
            seen.append((second, stub.url, response.status_code, response.text))
    return seen


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_cada_escenario_se_reproduce_igual_dos_veces(name):
    assert replay(name) == replay(name)


def test_nunca_en_produccion():
    with pytest.raises(ScenarioNotAllowed):
        simulated_transport("partido_en_vivo", SteppingClock(START), app_env="production")


def test_escenario_desconocido():
    with pytest.raises(KeyError):
        simulated_transport("no_existe", SteppingClock(START), app_env="development")


def test_todos_los_escenarios_usan_datos_marcados_como_ficticios():
    # Plan D-16 de la 002: nada inventado puede confundirse con datos reales de la liga.
    import json
    import re
    names = set()
    for build in SCENARIOS.values():
        for stub in build().stubs:
            names |= set(re.findall(r'"(?:name|player_tag)": "([^"]+)"', stub.body))
            names |= set(re.findall(r'title="[^"]*">([^<]+)</a>', stub.body.replace('\\"', '"')))
    team_and_player_names = {n for n in names if not n.startswith(("CDL ", "Major ", "Hardpoint", "Search", "Overload"))
                             and n not in {"Colossus", "Raid", "Den", "Exposure"}}
    assert team_and_player_names and all(n.startswith("[FICTICIO]") for n in team_and_player_names), team_and_player_names


def status_at(client, clock, second):
    clock.advance(START.timestamp() + second - clock.instant.timestamp())
    result = bp.consult_regular(client, observed_at=clock.now())
    match = next((r for r in result.records if r["kind"] == "match"), None)
    return result, match


def test_partido_en_vivo_programado_en_vivo_y_terminado():
    client, _, clock = client_for("partido_en_vivo")
    _, match = status_at(client, clock, 10)
    assert match["status"] == "scheduled"
    _, match = status_at(client, clock, 200)
    assert (match["status"], match["maps_won"]) == ("live", [1, 0])
    _, match = status_at(client, clock, 400)
    assert (match["status"], match["maps_won"], match["winner_side"]) == ("finished", [3, 1], 1)
    detail = bp.consult_match(client, 900, observed_at=clock.now(), job="finished_matches")
    maps = [(r["position"], r["status"]) for r in detail.records if r["kind"] == "match_map"]
    assert maps == [(1, "played"), (2, "played"), (3, "played"), (4, "played"), (5, "not_played")]


def test_fuente_caida_y_recuperada():
    client, _, clock = client_for("fuente_caida")
    result, _ = status_at(client, clock, 10)
    assert result.outcome == "failure" and "503" in result.message
    result, match = status_at(client, clock, 200)
    assert result.outcome == "success" and match["source_id"] == "902"


def test_respuesta_vacia_cuenta_cero_elementos():
    client, _, clock = client_for("respuesta_vacia")
    result, _ = status_at(client, clock, 10)
    assert result.item_count == 2
    result, _ = status_at(client, clock, 70)
    assert result.item_count == 0


def test_varios_partidos_en_vivo():
    client, _, clock = client_for("varios_en_vivo")
    result, _ = status_at(client, clock, 10)
    live = [r for r in result.records if r["kind"] == "match" and r.get("status") == "live"]
    assert len(live) == 3


def test_ningun_escenario_simula_la_wiki():
    # Spec 003, C-18: Retake no consulta la Wiki (I-26).
    from app.sources.simulated import hosts

    assert not any("fandom" in host for host in hosts())


# --- Revisión de F5: consultas que el proceso de obtención necesita del conector (plan §5) -------


class Recording:
    """Envuelve el transporte simulado y anota cada petición."""

    def __init__(self, transport):
        self.transport, self.calls = transport, []

    def __call__(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, SimulatedParams.of(params)))
        return self.transport(url, params=params, headers=headers, timeout=timeout)


class SimulatedParams:
    @staticmethod
    def of(params):
        import json

        params = dict(params or {})
        if "input" in params:
            params.update(json.loads(params["input"]).get("json") or {})
        return params


def recording_client(name):
    clock = SteppingClock(START)
    transport = Recording(simulated_transport(name, clock, app_env="development"))
    return PoliteClient("bp", transport, clock=clock, sleep=clock.sleep, base_url=bp.BASE_URL), transport, clock


def test_el_listado_indica_los_equipos_y_las_fechas_de_la_temporada_actual():
    # RF-18: el "Resto" sigue con las fichas de equipo y de jugador, que necesitan ambos datos.
    from app.sources.simulated import SEASON_2026, TEAMS

    client, _, clock = recording_client("partido_en_vivo")
    result = bp.consult_regular(client, clock.now())
    assert result.teams == tuple(str(t["id"]) for t in TEAMS)
    assert result.season == (2026, SEASON_2026["start_date"], SEASON_2026["end_date"])


def test_la_lista_de_proximos_y_en_vivo_no_pide_los_partidos_terminados():
    # Plan §5: "Antes del partido" y la lista de "En vivo" consultan solo la lista.
    client, transport, clock = recording_client("partido_en_vivo")
    result = bp.consult_upcoming(client, clock.now(), job="pre_match")
    statuses = {params.get("status") for url, params in transport.calls if "fetchMatchesPage" in url}
    assert statuses == {"upcoming_live"}
    assert result.outcome == "success"
    assert [r["source_id"] for r in result.records if r["kind"] == "match"] == ["900"]
    assert result.item_count == 1


def test_cada_escenario_responde_las_fichas_de_equipo_y_de_jugador():
    # Sin ellas, el "Resto" fallaría siempre en modo simulado (RF-18).
    from app.sources.simulated import SEASON_2026

    for name in SCENARIOS:
        client, _, clock = recording_client(name)
        result = bp.consult_teams(client, ["4", "743"], (2026, SEASON_2026["start_date"], SEASON_2026["end_date"]),
                                  clock.now())
        kinds = [r["kind"] for r in result.records]
        assert result.outcome == "success", name
        assert kinds.count("standing") == 2 and "player" in kinds and "roster" in kinds, name


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_cada_partido_en_vivo_o_terminado_tiene_su_pagina(name):
    # El trabajador consulta la página de cada partido en vivo o terminado (RF-16, RF-19): sin
    # ella, el recorrido manual en modo simulado registraría siempre un 404 (T-057).
    import json

    clock = SteppingClock(START)
    transport = simulated_transport(name, clock, app_env="development")
    missing = []
    for stub in transport.scenario.stubs:
        if "fetchMatchesPage" not in stub.url or stub.status != 200:
            continue
        clock.advance(START.timestamp() + stub.start - clock.instant.timestamp())
        for match in json.loads(stub.body)["result"]["data"]["json"]["data"]:
            if match["status"] in ("live", "complete"):
                response = transport(f"{bp.BASE_URL}/match/{match['id']}")
                if response.status_code != 200 or '"status": "' + match["status"] + '"' not in response.text:
                    missing.append((match["id"], match["status"], stub.start))
    assert missing == []
