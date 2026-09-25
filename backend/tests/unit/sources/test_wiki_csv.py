"""T-096 · Lectura y conversión de los archivos CSV de la Wiki (spec 003: RF-4 a RF-4c; plan I-26).

Los CSV de prueba son ficticios pero tienen las mismas columnas que los de `CDL-data-analysis`.
"""

import csv
from datetime import UTC, datetime

import pytest

from app.ingest.records import parse_record
from app.sources import wiki_csv
from app.sources.wiki_csv import WikiCsvError, read_wiki_csv

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
HISTORY_COLUMNS = ["Place", "Year", "Game Version", "final_date", "Prize", "Prize (%)", "Team", "Player"]
BIRTHDAY_COLUMNS = ["Player", "Name", "Birthday"]
ROSTER_COLUMNS = ["Team", "Role", "ID", "Country", "Name", "Current Team", "Current Role", "Stream", "Twitter",
                  "Birthday", "Age"]


def write(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def history_row(place, year, team, player, prize="$ 400,000", percent="40%", game="Black Ops 7", final="2026-06-28"):
    return [place, year, game, final, prize, percent, team, player]


@pytest.fixture
def folder(tmp_path):
    write(tmp_path / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2026", "[FICTICIO] Alfa", "[FICTICIO] Uno"),
        history_row("1", "2026", "[FICTICIO] Alfa", "[FICTICIO] Dos"),
        history_row("2", "2026", "[FICTICIO] Beta", "[FICTICIO] Tres", prize="$ 240,000", percent="24%"),
        history_row("9-12", "2026", "[FICTICIO] Gamma", "[FICTICIO] Cuatro", prize="", percent=""),
        history_row("DQ", "2019", "[FICTICIO] Alfa", "[FICTICIO] Uno", prize="-", percent="-",
                    game="Black Ops 4", final="2019-08-18"),
    ])
    write(tmp_path / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [
        ["[FICTICIO] Uno", "[FICTICIO] Nombre Uno", "2000-01-02"],
        ["[FICTICIO] Fuera", "[FICTICIO] Nombre Fuera", "1999-03-04"],   # ni en el historial ni en un roster
    ])
    write(tmp_path / "cdl_2026_rosters.csv", ROSTER_COLUMNS, [
        ["[FICTICIO] Alfa", "", "[FICTICIO] Cinco", "Mexico", "[FICTICIO] Nombre Cinco", "", "Player",
         "https://twitch.tv/x", "cinco_tw", "2003-05-06", "23.0"],
    ])
    return tmp_path


def kinds(records, kind):
    return [r for r in records if r["kind"] == kind]


def by_id(records, kind):
    return {r["source_id"]: r for r in kinds(records, kind)}


def test_todos_los_registros_cumplen_el_contrato_de_la_002(folder):
    data = read_wiki_csv(folder, NOW)
    for record in data.records:
        parse_record(record)
        assert record["source"] == "wiki"
    assert data.problems == []


def test_una_clasificacion_por_anio_y_equipo_con_su_roster_y_el_premio_del_equipo(folder):
    placements = by_id(read_wiki_csv(folder, NOW).records, "placement")
    alfa = placements["Call_of_Duty_League_Championship_2026/[FICTICIO]_Alfa"]
    assert (alfa["place"], alfa["prize_usd"], alfa["pool_percent"]) == ("1", 400000, 40)
    assert [e["gamertag_at_final"] for e in alfa["roster"]] == ["[FICTICIO] Uno", "[FICTICIO] Dos"]
    assert alfa["roster"][0]["player_ref"] == "wiki:[FICTICIO]_Uno"
    assert alfa["franchise_ref"] == "wiki:[FICTICIO]_Alfa"
    assert alfa["published_team_name"] == "[FICTICIO] Alfa"
    assert len(placements) == 4  # nunca una fila por jugador (RF-7 de la 002)


def test_lugares_con_rango_y_dq_tal_cual_y_premios_vacios_ausentes(folder):
    placements = by_id(read_wiki_csv(folder, NOW).records, "placement")
    gamma = placements["Call_of_Duty_League_Championship_2026/[FICTICIO]_Gamma"]
    assert gamma["place"] == "9-12" and "prize_usd" not in gamma and "pool_percent" not in gamma
    dq = placements["Call_of_Duty_World_League_Championship_2019/[FICTICIO]_Alfa"]
    assert dq["place"] == "DQ" and "prize_usd" not in dq


def test_campeonatos_con_pagina_competicion_juego_fecha_y_completado(folder):
    championships = by_id(read_wiki_csv(folder, NOW).records, "championship")
    c2026 = championships["Call_of_Duty_League_Championship_2026"]
    assert (c2026["year"], c2026["competition"]) == (2026, "Call of Duty League Championship")
    assert (c2026["game_name"], c2026["game_abbreviation"]) == ("Call of Duty: Black Ops 7", "BO7")
    assert (c2026["final_date"], c2026["completed"]) == ("2026-06-28", True)
    c2019 = championships["Call_of_Duty_World_League_Championship_2019"]
    assert c2019["competition"] == "Call of Duty World League Championship"
    assert "completed" not in c2019  # sin 1.er puesto en el archivo


def test_franquicias_e_identidades_por_nombre_de_equipo(folder):
    records = read_wiki_csv(folder, NOW).records
    assert set(by_id(records, "franchise")) == {"[FICTICIO]_Alfa", "[FICTICIO]_Beta", "[FICTICIO]_Gamma"}
    identity = by_id(records, "identity")["[FICTICIO]_Alfa#identity"]
    assert (identity["franchise_ref"], identity["short_name"]) == ("wiki:[FICTICIO]_Alfa", "[FICTICIO] Alfa")
    order = [r["kind"] for r in records]
    assert order.index("franchise") < order.index("placement") and order.index("player") < order.index("placement")


def test_cada_nombre_vale_desde_el_dia_siguiente_a_la_final_anterior_a_su_primer_campeonato(tmp_path):
    # Plan I-45: la Wiki no publica cuándo cambia un nombre; se deduce de los campeonatos (RF-74 de la 002).
    write(tmp_path / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2020", "[FICTICIO] Viejo", "[FICTICIO] Uno", final="2020-08-30"),
        history_row("3", "2021", "[FICTICIO] Viejo", "[FICTICIO] Uno", final="2021-08-22"),
        history_row("4", "2022", "[FICTICIO] Nuevo", "[FICTICIO] Uno", final="2022-08-07"),
        history_row("2", "2026", "[FICTICIO] Nuevo", "[FICTICIO] Uno", final="2026-07-19"),
        history_row("5", "2026", "[FICTICIO] Otro", "[FICTICIO] Dos", final="2026-07-19"),
    ])
    write(tmp_path / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [])
    identities = by_id(read_wiki_csv(tmp_path, NOW).records, "identity")
    # Sin final del año anterior (2019 y 2025 no están), desde el 1 de enero de su primer año.
    assert identities["[FICTICIO]_Viejo#identity"]["valid_from"] == "2020-01-01T00:00:00+00:00"
    assert identities["[FICTICIO]_Nuevo#identity"]["valid_from"] == "2021-08-23T00:00:00+00:00"
    assert identities["[FICTICIO]_Otro#identity"]["valid_from"] == "2026-01-01T00:00:00+00:00"


def test_los_equipos_de_los_rosters_tambien_son_identidades_de_la_wiki(tmp_path):
    # Cambio C-28: el roster de la temporada trae el nombre de una franquicia que aún no ha jugado un Champs.
    write(tmp_path / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2024", "[FICTICIO] Viejo", "[FICTICIO] Uno", final="2024-07-21"),
        history_row("2", "2025", "[FICTICIO] Alfa", "[FICTICIO] Dos", final="2025-06-29"),
    ])
    write(tmp_path / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [])
    write(tmp_path / "cdl_2026_rosters.csv", ROSTER_COLUMNS, [
        ["[FICTICIO] Nuevo", "", "[FICTICIO] Uno", "", "", "", "", "", "", "", ""],
        ["[FICTICIO] Alfa", "", "[FICTICIO] Dos", "", "", "", "", "", "", "", ""],
        ["", "", "[FICTICIO] Tres", "", "", "", "", "", "", "", ""],
    ])
    records = read_wiki_csv(tmp_path, NOW).records
    assert set(by_id(records, "franchise")) == {"[FICTICIO]_Viejo", "[FICTICIO]_Alfa", "[FICTICIO]_Nuevo"}
    identities = by_id(records, "identity")
    nuevo = identities["[FICTICIO]_Nuevo#identity"]
    assert (nuevo["franchise_ref"], nuevo["short_name"]) == ("wiki:[FICTICIO]_Nuevo", "[FICTICIO] Nuevo")
    assert nuevo["valid_from"] == "2025-06-30T00:00:00+00:00"
    # Un nombre que ya estaba en el historial vale desde su primer Champs, no desde el roster.
    assert identities["[FICTICIO]_Alfa#identity"]["valid_from"] == "2024-07-22T00:00:00+00:00"
    assert "placement" not in {r["kind"] for r in records if r["source_id"].endswith("[FICTICIO]_Nuevo")}


def test_sin_fecha_legible_de_la_final_anterior_el_nombre_vale_desde_el_1_de_enero(tmp_path):
    write(tmp_path / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2021", "[FICTICIO] Viejo", "[FICTICIO] Uno", final="agosto"),
        history_row("4", "2022", "[FICTICIO] Nuevo", "[FICTICIO] Uno", final="2022-08-07"),
    ])
    write(tmp_path / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [])
    identities = by_id(read_wiki_csv(tmp_path, NOW).records, "identity")
    assert identities["[FICTICIO]_Nuevo#identity"]["valid_from"] == "2022-01-01T00:00:00+00:00"


def test_datos_personales_solo_de_jugadores_del_historial_o_de_un_roster(folder):
    players = by_id(read_wiki_csv(folder, NOW).records, "player")
    assert "[FICTICIO]_Fuera" not in players  # RF-4a
    uno = players["[FICTICIO]_Uno"]
    assert (uno["gamertag"], uno["real_name"], uno["birth_date"]) == ("[FICTICIO] Uno", "[FICTICIO] Nombre Uno", "2000-01-02")
    cinco = players["[FICTICIO]_Cinco"]
    assert (cinco["country"], cinco["real_name"], cinco["birth_date"]) == ("Mexico", "[FICTICIO] Nombre Cinco", "2003-05-06")
    assert set(players["[FICTICIO]_Dos"]) == {"kind", "source", "source_id", "observed_at", "gamertag"}


def test_los_datos_personales_no_pasan_a_otro_gamertag_que_solo_cambia_en_mayusculas(tmp_path):
    # Plan I-46: en la Wiki, LuCkY (Champs 2013) y Lucky (roster 2026) son personas distintas.
    write(tmp_path / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("6", "2013", "[FICTICIO] Viejo", "[FICTICIO] LuCkY", final="2013-04-07"),
        history_row("1", "2026", "[FICTICIO] Alfa", "[FICTICIO] Lucky"),
    ])
    write(tmp_path / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [["[FICTICIO] Lucky", "[FICTICIO] Nombre Lucky", "2001-02-03"]])
    write(tmp_path / "cdl_2026_rosters.csv", ROSTER_COLUMNS, [
        ["[FICTICIO] Alfa", "", "[FICTICIO] Lucky", "Spain", "", "", "", "", "", "", ""],
    ])
    players = by_id(read_wiki_csv(tmp_path, NOW).records, "player")
    lucky = players["[FICTICIO]_Lucky"]
    assert (lucky["real_name"], lucky["birth_date"], lucky["country"]) == ("[FICTICIO] Nombre Lucky", "2001-02-03", "Spain")
    assert set(players["[FICTICIO]_LuCkY"]) == {"kind", "source", "source_id", "observed_at", "gamertag"}


def test_sin_otro_gamertag_parecido_los_datos_personales_se_asignan_sin_distinguir_mayusculas(tmp_path):
    write(tmp_path / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [history_row("1", "2026", "[FICTICIO] Alfa", "[FICTICIO] Uno")])
    write(tmp_path / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [["[FICTICIO] UNO", "[FICTICIO] Nombre Uno", "2000-01-02"]])
    write(tmp_path / "cdl_2026_rosters.csv", ROSTER_COLUMNS, [
        ["[FICTICIO] Alfa", "", "[FICTICIO] Uno", "Mexico", "", "", "", "", "", "", ""],
    ])
    players = by_id(read_wiki_csv(tmp_path, NOW).records, "player")
    uno = players["[FICTICIO]_Uno"]
    assert (uno["real_name"], uno["birth_date"], uno["country"]) == ("[FICTICIO] Nombre Uno", "2000-01-02", "Mexico")


def test_redes_sociales_y_edad_nunca_se_leen(folder):
    text = repr(read_wiki_csv(folder, NOW).records)
    assert "twitch" not in text and "cinco_tw" not in text and "23.0" not in text


def test_un_premio_o_una_fecha_ilegibles_se_marcan_sin_perder_la_fila(folder):
    write(folder / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2026", "[FICTICIO] Alfa", "[FICTICIO] Uno", prize="mucho dinero", final="28/06/2026"),
    ])
    records = read_wiki_csv(folder, NOW).records
    (placement,) = kinds(records, "placement")
    assert placement["unreadable"] == ["prize_usd"]
    (championship,) = kinds(records, "championship")
    assert championship["unreadable"] == ["final_date"]


def test_una_fila_con_un_anio_no_valido_se_descarta_y_se_informa(folder):
    write(folder / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2026", "[FICTICIO] Alfa", "[FICTICIO] Uno"),
        history_row("1", "dos mil", "[FICTICIO] Beta", "[FICTICIO] Tres"),
    ])
    data = read_wiki_csv(folder, NOW)
    assert len(kinds(data.records, "placement")) == 1
    assert data.problems == [f"{wiki_csv.HISTORY_FILE}, fila 3: año no válido: 'dos mil'"]


@pytest.mark.parametrize("missing", [wiki_csv.HISTORY_FILE, wiki_csv.BIRTHDAYS_FILE])
def test_un_archivo_obligatorio_que_falta_es_un_error_que_lo_nombra(folder, missing):
    (folder / missing).unlink()
    with pytest.raises(WikiCsvError, match=missing):
        read_wiki_csv(folder, NOW)


def test_una_columna_que_falta_es_un_error_que_nombra_archivo_y_columna(folder):
    write(folder / "cdl_2026_rosters.csv", ["Team", "ID", "Name"], [["[FICTICIO] Alfa", "[FICTICIO] Cinco", "x"]])
    with pytest.raises(WikiCsvError, match=r"cdl_2026_rosters\.csv.*Birthday.*Country"):
        read_wiki_csv(folder, NOW)


def test_sin_archivos_de_rosters_tambien_se_importa(folder):
    (folder / "cdl_2026_rosters.csv").unlink()
    assert "[FICTICIO]_Cinco" not in by_id(read_wiki_csv(folder, NOW).records, "player")


def test_una_carpeta_que_no_existe_es_un_error(tmp_path):
    with pytest.raises(WikiCsvError, match="no existe"):
        read_wiki_csv(tmp_path / "nada", NOW)
