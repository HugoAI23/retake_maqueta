"""C-23 · Equipos invitados en la API (spec 002: RF-117a a RF-117c; plan I-38).

Se ven solo en sus partidos, marcados como invitados: nunca en la tabla ni en las listas de
franquicias o de jugadores de la temporada.
"""

from tests.integration.api.test_003_api import api, ingest, rec  # noqa: F401 — `api` es un fixture


def guests_world():
    return [
        rec("season", "s26", year=2026, name="CDL 2026"),
        rec("event", "e1", season_year=2026, name="[FICTICIO] Minor"),
        rec("franchise", "t1", guest=False), rec("identity", "t1-id", franchise_ref="bp:t1", short_name="[FICTICIO] Liga"),
        rec("franchise", "g1", guest=True), rec("identity", "g1-id", franchise_ref="bp:g1", short_name="[FICTICIO] Invitado"),
        rec("player", "p1", gamertag="[FICTICIO] De la liga"),
        rec("player", "p2", gamertag="[FICTICIO] Del invitado", real_name="[FICTICIO] Nombre"),
        rec("roster", "r1", season_year=2026, franchise_ref="bp:t1", player_ref="bp:p1", **{"from": "2025-11-01T00:00:00Z"}),
        rec("roster", "r2", season_year=2026, franchise_ref="bp:g1", player_ref="bp:p2", **{"from": "2025-11-01T00:00:00Z"}),
        rec("standing", "st1", season_year=2026, franchise_ref="bp:t1", position=1, points=100),
        rec("standing", "st2", season_year=2026, franchise_ref="bp:g1", position=2, points=50),
        rec("match", "m1", event_ref="bp:e1", best_of=5, status="finished", scheduled_at="2026-01-10T11:00:00Z",
            slots=[{"franchise_ref": "bp:t1"}, {"franchise_ref": "bp:g1"}], maps_won=[3, 0], winner_side=1),
        rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played", score=[250, 100],
            winner_side=1),
        rec("player_map_stats", "s1", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=20),
        rec("player_map_stats", "s2", map_ref="bp:mp1", player_ref="bp:p2", franchise_ref="bp:g1", kills=15),
    ]


def test_los_invitados_no_salen_en_la_lista_de_franquicias(api, clean_db):
    ingest(clean_db, guests_world())
    names = [f["identities"][-1]["shortName"] for f in api.get("/api/franchises").json()]
    assert names == ["[FICTICIO] Liga"]


def test_los_invitados_nunca_salen_en_la_tabla(api, clean_db):
    ingest(clean_db, guests_world())
    assert [row["identity"]["shortName"] for row in api.get("/api/standings").json()] == ["[FICTICIO] Liga"]


def test_los_jugadores_de_los_invitados_no_salen_en_la_lista_de_jugadores(api, clean_db):
    ingest(clean_db, guests_world())
    assert [p["currentGamertag"] for p in api.get("/api/players").json()] == ["[FICTICIO] De la liga"]


def test_un_jugador_de_la_liga_que_jugo_con_un_invitado_sigue_en_la_lista(api, clean_db):
    ingest(clean_db, [*guests_world(),
                      rec("roster", "r3", season_year=2026, franchise_ref="bp:g1", player_ref="bp:p1",
                          **{"from": "2025-10-28T00:00:00Z", "to": "2025-11-01T00:00:00Z"})])
    assert "[FICTICIO] De la liga" in [p["currentGamertag"] for p in api.get("/api/players").json()]


def test_en_sus_partidos_se_ven_marcados_como_invitados_con_sus_estadisticas(api, clean_db):
    ingest(clean_db, guests_world())
    (match,) = api.get("/api/matches").json()
    assert [(s["identity"]["shortName"], s["isGuest"]) for s in match["slots"]] == [
        ("[FICTICIO] Liga", False), ("[FICTICIO] Invitado", True)]
    assert sorted(s["kills"] for s in match["maps"][0]["stats"]) == [15, 20]


def test_la_ficha_de_un_jugador_invitado_se_puede_abrir_desde_su_partido(api, clean_db):
    ingest(clean_db, guests_world())
    (match,) = api.get("/api/matches").json()
    guest_stats = next(s for s in match["maps"][0]["stats"] if s["kills"] == 15)
    player = api.get(f"/api/players/{guest_stats['playerId']}").json()
    assert (player["realName"], player["teamIsGuest"]) == ("[FICTICIO] Nombre", True)
