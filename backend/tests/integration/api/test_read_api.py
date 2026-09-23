"""T-049 a T-057 · API de solo lectura (plan §1.4 y §2.3)."""


def get(api, path, status=200):
    response = api.get(path)
    assert response.status_code == status, response.text
    return response.json()


def keys_deep(value):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key
            yield from keys_deep(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from keys_deep(inner)


# --- T-050 · Temporada -----------------------------------------------------------------------

def test_temporada_actual(api):
    body = get(api, "/api/season/current")
    assert (body["year"], body["name"]) == (2026, "Call of Duty League 2026")
    assert body["startedAt"].endswith("Z")


# --- T-051 · Franquicias ---------------------------------------------------------------------

def test_franquicias_con_identidades_ordenadas(api, ids):
    franchises = {f["id"]: f for f in get(api, "/api/franchises")}
    faze = franchises[ids("franchise", "wiki:FaZe_Vegas")]
    assert [i["shortName"] for i in faze["identities"]] == ["ATL FaZe", "FaZe VGS"]
    assert faze["identities"][1]["validFrom"] == "2025-09-19T00:00:00Z"
    assert faze["identities"][1]["logoUrl"] is None
    assert set(faze["identities"][0]) == {"id", "shortName", "abbreviation", "logoUrl", "primaryColor", "secondaryColor", "validFrom"}


# --- T-052 · Jugadores -----------------------------------------------------------------------

def test_jugador_real_completo(api, ids):
    simp = get(api, f"/api/players/{ids('player', 'wiki:Simp')}")
    assert simp["currentGamertag"] == "Simp"
    assert simp["previousGamertags"] == ["Simplicity"]
    assert simp["realName"] == "Chris Lehr"
    assert simp["age"] == {"min": 25, "max": 25}
    assert simp["role"] is None
    assert simp["teamFranchiseId"] == ids("franchise", "wiki:FaZe_Vegas")
    assert (simp["isCurrentSeason"], simp["isFreeAgent"]) == (True, False)
    assert len(simp["championshipIds"]) == 2  # 2021 y 2026


def test_ninguna_respuesta_de_jugadores_contiene_la_fecha_ni_el_anio_de_nacimiento(api, ids):
    players = get(api, "/api/players")
    assert len(players) == 60
    for key in keys_deep(players):
        assert "birth" not in key.lower()
    detail = get(api, f"/api/players/{ids('player', 'wiki:Simp')}")
    assert not any("birth" in key.lower() for key in keys_deep(detail))


def test_edades_rango_y_datos_retirados(api, ids):
    assert get(api, f"/api/players/{ids('player', 'bp:fx-Year')}")["age"] == {"min": 22, "max": 23}
    assert get(api, f"/api/players/{ids('player', 'bp:fx-Age')}")["age"] == {"min": 20, "max": 21}
    removed = get(api, f"/api/players/{ids('player', 'bp:fx-Removed')}")
    assert (removed["realName"], removed["country"], removed["age"]) == (None, None, None)


def test_agente_libre_y_rol(api, ids):
    free = get(api, f"/api/players/{ids('player', 'bp:fx-Free')}")
    assert (free["isFreeAgent"], free["teamFranchiseId"]) == (True, None)
    assert get(api, f"/api/players/{ids('player', 'bp:fx-A1')}")["role"] == "SMG"


# --- T-053 · Eventos -------------------------------------------------------------------------

def test_eventos_de_la_temporada_actual(api):
    names = {e["name"]: e["seasonYear"] for e in get(api, "/api/events")}
    assert names == {"Call of Duty League Championship 2026": 2026, "[FICTICIO] Evento de casos límite": 2026}


# --- T-054 · Partidos ------------------------------------------------------------------------

def test_gran_final_real(api, ids):
    gf = get(api, f"/api/matches/{ids('match', 'wiki:Call_of_Duty_League_Championship_2026/Grand_Finals')}")
    assert (gf["phase"], gf["bestOf"], gf["status"], gf["winnerSide"]) == ("grand_final", 9, "finished", 1)
    assert gf["mapsWon"] == [5, 2]
    assert gf["scheduledAt"] == "2026-07-19T22:00:00Z"
    assert [s["identity"]["shortName"] for s in gf["slots"]] == ["FaZe VGS", "OpTic TEX"]
    assert [m["played"] for m in gf["maps"]] == [True] * 7 + [False] * 2
    not_played = gf["maps"][7]
    assert (not_played["mapName"], not_played["score"], not_played["stats"]) == ("Gridlock", None, [])
    simp = next(s for s in gf["maps"][1]["stats"] if s["playerId"] == ids("player", "wiki:Simp"))
    assert (simp["kills"], simp["firstBloods"], simp["kd"], simp["damage"], simp["hillTime"]) == (8, 3, 1.33, None, None)


def test_partidos_con_casos_limite(api, ids):
    def match(ref):
        return get(api, f"/api/matches/{ids('match', ref)}")

    main = match("bp:fx-main")
    assert main["maps"][0]["correctedFields"] == ["score_2"]
    assert [m["position"] for m in main["maps"]] == [1, 2, 3, 4, 5]

    origin = match("bp:fx-tbd-origin")
    assert origin["slots"][0]["origin"] == {"matchId": ids("match", "bp:fx-main"), "outcome": "winner"}
    assert (origin["slots"][0]["franchiseId"], origin["slots"][0]["identity"]) == (None, None)

    none = match("bp:fx-tbd-none")
    assert all(s == {"franchiseId": None, "identity": None, "origin": None} for s in none["slots"])

    live = match("bp:fx-live")
    assert (live["status"], live["mapsWon"], live["liveMap"]) == ("live", [0, 0], {"mode": None, "score": None})

    postponed = match("bp:fx-postponed")
    assert postponed["scheduleHistory"] == ["2026-10-01T18:00:00Z", "2026-10-02T18:00:00Z"]
    assert postponed["scheduledAt"] == "2026-10-02T18:00:00Z"

    assert match("bp:fx-unknown")["phase"] is None
    forfeit = match("bp:fx-forfeit")
    assert (forfeit["status"], forfeit["mapsWon"], forfeit["maps"]) == ("finished", [3, 0], [])


def test_lista_de_partidos_ordenada_por_horario(api):
    matches = get(api, "/api/matches")
    assert len(matches) == 8
    dates = [m["scheduledAt"] for m in matches]
    assert dates == sorted(dates)


# --- T-055 · Tabla de posiciones -------------------------------------------------------------

def test_tabla_de_posiciones(api):
    rows = get(api, "/api/standings")
    assert len(rows) == 14
    assert (rows[0]["identity"]["shortName"], rows[0]["position"], rows[0]["points"]) == ("OpTic TEX", 1, 575)
    assert [r["position"] for r in rows[-2:]] == [13, 13]


# --- T-056 · Historial -----------------------------------------------------------------------

def test_historial_de_campeonatos(api, ids):
    championships = get(api, "/api/championships")
    assert [c["year"] for c in championships] == [2026, 2025, 2021, 2020, 2014, 2013]
    champs_2026 = championships[0]
    assert [p["place"] for p in champs_2026["placements"]] == ["1", "2", "3", "4", "5-6", "5-6", "7-8", "7-8"]
    faze = champs_2026["placements"][0]
    assert (faze["identity"]["shortName"], faze["prizeUsd"], faze["poolPercent"], faze["isDq"]) == ("FaZe VGS", 800000, 40, False)
    assert {r["gamertagAtFinal"] for r in faze["roster"]} == {"Simp", "Drazah", "04", "Abuzah"}
    assert all(r["currentGamertag"] for r in faze["roster"])
    assert championships[2]["placements"][0]["identity"]["shortName"] == "ATL FaZe"
    assert championships[4]["placements"][-1]["place"] == "DQ"
    assert (championships[0]["gameName"], championships[0]["gameAbbreviation"], championships[0]["finalDate"]) == (
        "Call of Duty: Black Ops 7", "BO7", "2026-07-19")


# --- T-057 · Errores y documentación ---------------------------------------------------------

def test_identificador_inexistente_da_404(api):
    missing = "00000000-0000-0000-0000-000000000000"
    for path in ("/api/players/", "/api/matches/"):
        assert api.get(path + missing).status_code == 404


def test_docs_disponible_fuera_de_produccion(api):
    assert api.get("/docs").status_code == 200
