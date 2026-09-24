"""T-025 · Cliente educado: identificación, pausa por fuente, tiempo de espera y normas para robots."""

import pytest

from app.sources.http import (
    USER_AGENT,
    Forbidden,
    PoliteClient,
    SourceUnavailable,
)
from tests.unit.sources.fakes import FakeResponse, FakeTransport, SteppingClock

ROBOTS = "https://breakingpoint.gg/robots.txt"
PAGE = "https://breakingpoint.gg/matches"


def make_client(routes, source="bp", clock=None):
    clock = clock or SteppingClock()
    transport = FakeTransport(routes, clock)
    return PoliteClient(source, transport, clock=clock, sleep=clock.sleep, base_url="https://breakingpoint.gg"), transport, clock


def test_se_identifica_como_retake_y_nunca_como_navegador():
    client, transport, _ = make_client({ROBOTS: FakeResponse(404), PAGE: FakeResponse(200, "ok")})
    client.get(PAGE)
    headers = transport.calls[-1]["headers"]
    assert headers["User-Agent"] == USER_AGENT
    assert USER_AGENT.startswith("Retake/") and "Mozilla" not in USER_AGENT
    assert transport.calls[-1]["timeout"] == 15


def test_respeta_la_pausa_minima_de_la_fuente():
    client, transport, clock = make_client({ROBOTS: FakeResponse(404), PAGE: FakeResponse(200, "ok")})
    client.get(PAGE)
    client.get(PAGE)
    page_calls = [c["at"] for c in transport.calls if c["url"] == PAGE]
    assert (page_calls[1] - page_calls[0]).total_seconds() >= 2


def test_si_ya_paso_la_pausa_no_espera():
    client, _, clock = make_client({ROBOTS: FakeResponse(404), PAGE: FakeResponse(200, "ok")})
    client.get(PAGE)
    clock.advance(30)
    clock.slept.clear()
    client.get(PAGE)
    assert clock.slept == []


def test_una_norma_para_robots_que_prohibe_la_ruta_impide_la_consulta():
    robots = FakeResponse(200, "User-agent: *\nDisallow: /matches\n")
    client, transport, _ = make_client({ROBOTS: robots, PAGE: FakeResponse(200, "ok")})
    with pytest.raises(Forbidden, match="Disallow"):
        client.get(PAGE)
    assert all(c["url"] != PAGE for c in transport.calls)


def test_sin_robots_txt_publicado_se_permite_y_se_lee_una_sola_vez():
    client, transport, _ = make_client({ROBOTS: FakeResponse(404), PAGE: FakeResponse(200, "ok")})
    client.get(PAGE)
    client.get(PAGE)
    assert sum(1 for c in transport.calls if c["url"] == ROBOTS) == 1


def test_robots_ilegible_no_bloquea_pero_queda_anotado():
    # La Wiki tapa su robots.txt con Cloudflare (403): no publica normas legibles.
    client, _, _ = make_client({ROBOTS: FakeResponse(403, "Just a moment..."), PAGE: FakeResponse(200, "ok")})
    assert client.get(PAGE).text == "ok"
    assert client.robots_unreadable


def test_un_error_http_es_fuente_no_disponible_con_mensaje_plano():
    client, _, _ = make_client({ROBOTS: FakeResponse(404), PAGE: FakeResponse(503, "<h1>Service Unavailable</h1>")})
    with pytest.raises(SourceUnavailable, match="503"):
        client.get(PAGE)


def test_un_fallo_de_red_es_fuente_no_disponible():
    client, _, _ = make_client({ROBOTS: FakeResponse(404), PAGE: ConnectionError("sin red")})
    with pytest.raises(SourceUnavailable, match="sin red"):
        client.get(PAGE)


def test_ya_no_hay_cliente_ni_espera_creciente_para_la_wiki():
    # Spec 003, C-18: Retake no consulta la Wiki; sus datos llegan por archivos (I-26).
    from app.sources import http

    assert not hasattr(http, "requests_transport")
    assert not hasattr(http.PoliteClient, "get_with_backoff")
    with pytest.raises(ValueError, match="wiki"):
        http.real_client("wiki")
