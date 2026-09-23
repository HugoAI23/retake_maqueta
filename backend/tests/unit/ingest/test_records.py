"""T-029 · Registros de fuente (RF-66, RF-129; plan §2.1)."""

import pytest

from app.ingest.records import RefKey, RecordError, parse_record

BASE = {"source": "bp", "source_id": "1", "observed_at": "2026-09-22T12:00:00Z"}

VALID = [
    {"kind": "season", "year": 2026, "name": "CDL 2026"},
    {"kind": "event", "season_year": 2026, "name": "Major 1"},
    {"kind": "franchise", "predecessor": "wiki:Old_Team"},
    {"kind": "identity", "franchise_ref": "bp:10", "short_name": "FaZe VGS", "abbreviation": "VGS"},
    {"kind": "player", "gamertag": "Simp", "previous_gamertags": ["Simpo"], "birth_year": 2000},
    {"kind": "roster", "season_year": 2026, "franchise_ref": "bp:10", "player_ref": "bp:20", "from": "2025-11-01T00:00:00Z"},
    {"kind": "match", "event_ref": "bp:30", "phase": "Winners Bracket", "best_of": 5, "status": "live",
     "scheduled_at": "2026-05-01T18:00:00Z",
     "slots": [{"franchise_ref": "bp:10"}, {"origin": {"match_ref": "bp:29", "outcome": "winner"}}],
     "maps_won": [1, 0], "live_map": {"mode": "Hardpoint", "score": [120, 80]}},
    {"kind": "match_map", "match_ref": "bp:31", "position": 1, "mode": "Hardpoint", "map_name": "Vault",
     "status": "played", "score": [250, 200], "winner_side": 1},
    {"kind": "player_map_stats", "map_ref": "bp:32", "player_ref": "bp:20", "franchise_ref": "bp:10",
     "kills": 25, "deaths": 20, "kd": 1.25, "hill_time": 90},
    {"kind": "standing", "season_year": 2026, "franchise_ref": "bp:10", "position": 1, "points": 240},
    {"kind": "championship", "year": 2026, "competition": "CDL Champs", "game_name": "Call of Duty: Black Ops 6",
     "game_abbreviation": "BO6", "final_date": "2026-06-28", "completed": True},
    {"kind": "placement", "championship_ref": "wiki:Champs_2026", "franchise_ref": "wiki:FaZe",
     "published_team_name": "FaZe Vegas", "place": "1", "prize_usd": 800000, "pool_percent": 40,
     "roster": [{"player_ref": "wiki:Simp", "gamertag_at_final": "Simp"}]},
]


@pytest.mark.parametrize("fields", VALID, ids=[f["kind"] for f in VALID])
def test_un_registro_valido_de_cada_tipo(fields):
    record = parse_record({**BASE, **fields})
    assert record.kind == fields["kind"]
    assert record.source == "bp"


def test_las_referencias_admiten_texto_y_objeto():
    assert RefKey.model_validate("wiki:Some_Page") == RefKey(source="wiki", source_id="Some_Page")
    assert RefKey.model_validate({"source": "cdl", "source_id": "x:y"}) == RefKey(source="cdl", source_id="x:y")


@pytest.mark.parametrize(
    "raw",
    [
        {**BASE, "kind": "season"},  # falta el año
        {**BASE, "kind": "unknown"},
        {**BASE, "kind": "season", "year": 2026, "source": "twitter"},
        {**BASE, "kind": "season", "year": 2026, "observed_at": "2026-09-22T12:00:00"},  # sin zona horaria
        {**BASE, "kind": "season", "year": 2026, "extra_field": 1},
        {**BASE, "kind": "match", "event_ref": "bp:1", "status": "paused"},
        {**BASE, "kind": "player", "gamertag": "X", "source_id": ""},
        "no es un objeto",
    ],
)
def test_un_registro_mal_formado_se_rechaza_con_su_motivo(raw):
    with pytest.raises(RecordError) as error:
        parse_record(raw)
    assert str(error.value)


def test_los_textos_se_conservan_byte_a_byte():
    gamertag = '  <script>alert("x")</script> Ñandú '
    record = parse_record({**BASE, "kind": "player", "gamertag": gamertag})
    assert record.gamertag == gamertag


def test_las_estadisticas_admiten_cualquier_valor_para_validarlo_despues():
    # Un valor imposible no rechaza el registro: se descarta solo ese dato (RF-100).
    record = parse_record({**BASE, "kind": "player_map_stats", "map_ref": "bp:1", "player_ref": "bp:2",
                           "franchise_ref": "bp:3", "kills": -5, "deaths": "abc"})
    assert record.kills == -5
    assert record.deaths == "abc"
