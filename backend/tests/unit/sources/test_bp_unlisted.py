"""C-22 y C-24 · Equipos que no están en la lista de la temporada (spec 003: RF-18a, RF-18b; plan I-36, I-38).

BreakingPoint lista a Boston Breach como M80 Boston y con otro número, pero sus partidos, su tabla y
sus rosters de 2026 siguen con el número antiguo. El conector consulta la ficha de cada equipo que
no está en `allTeams`: si está en la tabla de esa temporada, es una franquicia; si no, un equipo
invitado (RF-117a de la 002).
"""

from app.sources import bp
from app.sources.simulated import GUEST_PLAYER, SEASON_2026
from tests.unit.sources.test_simulated import recording_client

SEASON = (2026, SEASON_2026["start_date"], SEASON_2026["end_date"])


def kinds_and_ids(result):
    return [(r["kind"], r["source_id"]) for r in result.records]


def records_by_key(result):
    return {(r["kind"], r["source_id"]): r for r in result.records}


def team_page_calls(transport, team_id):
    return sum(1 for url, _ in transport.calls if url.endswith(f"/teams/{team_id}"))


def test_un_equipo_sin_listar_que_esta_en_la_tabla_se_registra_como_franquicia():
    client, _, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_regular(client, clock.now())
    records = records_by_key(result)
    assert records[("franchise", "6")]["guest"] is False
    identity = records[("identity", "6#identity")]
    assert identity["franchise_ref"] == "bp:6"
    assert (identity["short_name"], identity["abbreviation"], identity["primary_color"]) == (
        "[FICTICIO] Boston Breach", "BOS", "#02FF5B")
    # Su fecha de alta en la fuente: así su identidad es anterior a la del nombre siguiente (I-36).
    assert identity["valid_from"] == "2021-12-15T00:00:00+00:00"
    assert records[("standing", "2026/standings/6")]["position"] == 5
    # Antes que los partidos, para que la ingesta ya la conozca.
    order = kinds_and_ids(result)
    assert order.index(("franchise", "6")) < order.index(("match", "911"))
    # Sus fichas de equipo se consultan en adelante como las de las demás (RF-18).
    assert "6" in result.teams


def test_las_franquicias_de_la_lista_no_son_invitadas():
    # RF-117d de la 002: si un invitado entra en la lista, deja de estar marcado como tal.
    client, _, clock = recording_client("franquicia_sin_listar")
    records = records_by_key(bp.consult_regular(client, clock.now()))
    assert records[("franchise", "4")]["guest"] is False


def test_un_equipo_fuera_de_la_tabla_se_registra_como_invitado():
    client, _, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_regular(client, clock.now())
    records = records_by_key(result)
    assert records[("franchise", "744")]["guest"] is True
    assert records[("identity", "744#identity")]["short_name"] == "[FICTICIO] Huntsmen"
    assert ("standing", "2026/standings/744") not in records  # nunca en la tabla (RF-117c de la 002)
    order = kinds_and_ids(result)
    assert order.index(("franchise", "744")) < order.index(("match", "912"))
    # Sus fichas no van con las del "Resto" cada hora: el trabajador las pide una vez al mes (RF-18b).
    assert "744" not in result.teams


def test_una_ficha_que_no_responde_se_anota_y_la_consulta_sigue():
    client, _, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_regular(client, clock.now())
    assert result.outcome == "partial"
    (rejection,) = [r for r in result.rejected if r.ref == "bp:745"]
    assert rejection.field == "team" and "404" in rejection.reason
    assert ("franchise", "6") in kinds_and_ids(result)


def test_los_invitados_ya_conocidos_no_se_vuelven_a_pedir_en_el_listado():
    # RF-18b: su ficha se pide al aparecer y después una vez al mes, no con cada listado.
    client, transport, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_regular(client, clock.now(), known_guests={"744"})
    assert team_page_calls(transport, 744) == 0
    assert ("franchise", "744") not in kinds_and_ids(result)
    assert ("match", "912") in kinds_and_ids(result)  # su partido sí: la franquicia ya existe
    # La franquicia sin listar se vuelve a comprobar en cada listado: su identidad puede cambiar.
    assert team_page_calls(transport, 6) == 1


def test_la_ficha_mensual_de_un_invitado_trae_su_identidad_y_sus_jugadores():
    client, _, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_teams(client, ["744"], SEASON, clock.now(), guests={"744"})
    records = records_by_key(result)
    assert records[("franchise", "744")]["guest"] is True
    assert records[("identity", "744#identity")]["short_name"] == "[FICTICIO] Huntsmen"
    player = records[("player", str(GUEST_PLAYER))]
    assert (player["real_name"], player["birth_date"]) == ("[FICTICIO] Invitado", "2004-05-06")  # RF-117b
    assert records[("roster", f"2026/744/{GUEST_PLAYER}")]["franchise_ref"] == "bp:744"


def test_la_ficha_de_una_franquicia_de_la_lista_no_trae_su_identidad():
    # La identidad de las franquicias de la lista sale del listado; la ficha solo aporta la tabla.
    client, _, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_teams(client, ["4"], SEASON, clock.now())
    assert not any(r["kind"] in ("franchise", "identity") for r in result.records)


def test_la_lista_de_proximos_y_en_vivo_tambien_reconoce_la_franquicia():
    client, _, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_upcoming(client, clock.now(), job="pre_match")
    order = kinds_and_ids(result)
    assert order.index(("franchise", "6")) < order.index(("match", "913"))


def test_sin_equipos_fuera_de_la_lista_no_se_pide_ninguna_ficha():
    client, transport, clock = recording_client("partido_en_vivo")
    bp.consult_regular(client, clock.now())
    assert not any("/teams/" in url for url, _ in transport.calls)
