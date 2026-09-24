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
