"""T-047 · Carga completa de los datos de prueba y resultado de cada caso.

Carga la muestra real, los ficticios y el archivo de curación del proyecto en
`retake_test`, y comprueba caso por caso lo que la spec 002 espera.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Championship,
    Franchise,
    Identity,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    Placement,
    PlacementRoster,
    Player,
    PlayerGamertag,
    PlayerMapStats,
    Standing,
)
from app.db.queries import championship_ids_for_player, current_season, is_free_agent
from app.ingest.fixtures import load_fixtures
from app.ingest.pipeline import ingest_records
from app.ingest.store import entity_for


@pytest.fixture(scope="module")
def loaded(tmp_path_factory):
    """Una sola carga para todo el módulo (la carga completa tarda unos segundos)."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from app.config import load_settings
    from app.db.session import make_engine
    from tests.conftest import BACKEND_DIR

    url = load_settings(app_env="test").test_database_url
    engine = make_engine(url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes.update(database_url=url, configure_logger=False)
    command.upgrade(config, "head")
    session = Session(engine)
    result = load_fixtures(session, app_env="test")
    session.commit()
    yield session, result
    session.close()
    engine.dispose()


@pytest.fixture
def s(loaded):
    session, _ = loaded
    session.expire_all()
    return session


def player(s, ref):
    return s.get(Player, entity_for(s, "player", ref))


def one(s, model, **where):
    return s.scalars(select(model).filter_by(**where)).one()


def identity_name(s, identity_id):
    return s.get(Identity, identity_id).short_name


# --- Carga -----------------------------------------------------------------------------------

def test_se_carga_todo_sin_rechazos(loaded):
    _, result = loaded
    assert result.report.rejected == []
    assert result.report.accepted == 178 + 75


def test_la_temporada_actual_es_2026(s):
    assert current_season(s).year == 2026


# --- Muestra real ----------------------------------------------------------------------------

def test_faze_vgs_2026_un_solo_premio_de_800000_con_cuatro_jugadores(s):
    champs = one(s, Championship, year=2026)
    faze = entity_for(s, "franchise", "wiki:FaZe_Vegas")
    placement = one(s, Placement, championship_id=champs.id, franchise_id=faze)
    assert (placement.place, placement.prize_usd, placement.pool_percent) == ("1", Decimal("800000"), Decimal("40"))
    assert s.scalar(select(func.count()).select_from(PlacementRoster).filter_by(placement_id=placement.id)) == 4
    assert identity_name(s, placement.identity_id) == "FaZe VGS"
    assert (champs.game_abbreviation, champs.final_date) == ("BO7", date(2026, 7, 19))


def test_lugares_compartidos_reales(s):
    champs = one(s, Championship, year=2026)
    places = s.scalars(select(Placement.place).filter_by(championship_id=champs.id)).all()
    assert places.count("5-6") == 2 and places.count("7-8") == 2


def test_plaza_continuada_y_identidad_de_su_fecha(s):
    assert entity_for(s, "franchise", "wiki:FaZe_Vegas") == entity_for(s, "franchise", "wiki:Atlanta_FaZe")
    assert entity_for(s, "franchise", "wiki:OpTic_Texas") == entity_for(s, "franchise", "wiki:Dallas_Empire")
    by_year = {s.get(Championship, p.championship_id).year: p for p in s.scalars(select(Placement).where(Placement.place == "1"))}
    assert identity_name(s, by_year[2021].identity_id) == "ATL FaZe"
    assert identity_name(s, by_year[2020].identity_id) == "DAL Empire"
    assert identity_name(s, by_year[2025].identity_id) == "OpTic TEX"


def test_simp_una_persona_con_datos_de_breakingpoint(s):
    simp = player(s, "wiki:Simp")
    assert simp.id == entity_for(s, "player", "bp:simp")
    assert (simp.real_name, simp.birth_date) == ("Chris Lehr", date(2001, 2, 6))
    assert s.scalars(select(PlayerGamertag.gamertag).filter_by(player_id=simp.id)).all() == ["Simplicity"]


def test_mismo_jugador_en_la_temporada_actual_y_en_el_historial(s):
    years = {s.get(Championship, cid).year for cid in championship_ids_for_player(s, player(s, "wiki:Abuzah").id)}
    assert years == {2025, 2026}


def test_gran_final_real_mapas_y_estadisticas(s):
    gf = s.get(Match, entity_for(s, "match", "wiki:Call_of_Duty_League_Championship_2026/Grand_Finals"))
    assert gf.id == entity_for(s, "match", "cdl:cdl-champs-2026-grand-finals")  # la web oficial es el mismo partido
    assert (gf.phase, gf.best_of, gf.maps_won_1, gf.maps_won_2, gf.winner_side) == ("grand_final", 9, 5, 2, 1)
    maps = s.scalars(select(MatchMap).filter_by(match_id=gf.id).order_by(MatchMap.position)).all()
    assert [m.played for m in maps] == [True] * 7 + [False] * 2
    assert (maps[7].map_name, maps[7].score_1) == ("Gridlock", None)
    stats = s.scalars(select(PlayerMapStats).where(PlayerMapStats.map_id == maps[1].id)).all()
    simp_snd = next(x for x in stats if x.player_id == player(s, "wiki:Simp").id)
    assert (simp_snd.kills, simp_snd.first_bloods, simp_snd.defuses, simp_snd.kd) == (8, 3, 2, Decimal("1.330"))
    assert simp_snd.damage is None  # la fuente no publica daño: ausente, no 0
    assert simp_snd.hill_time is None  # no es una estadística de Search & Destroy


def test_tabla_real_de_2026(s):
    faze = entity_for(s, "franchise", "wiki:FaZe_Vegas")
    row = one(s, Standing, franchise_id=faze)
    assert (row.position, row.points) == (3, 440)


# --- Casos ficticios ---------------------------------------------------------------------------

def match_of(s, ref):
    return s.get(Match, entity_for(s, "match", ref))


def test_forfeit(s):
    m = match_of(s, "bp:fx-forfeit")
    assert (m.status, m.maps_won_1, m.winner_side, m.went_live_at) == ("finished", 3, 1, None)
    assert s.scalars(select(MatchMap).filter_by(match_id=m.id)).all() == []


def test_aplazamiento_y_cancelacion(s):
    m = match_of(s, "bp:fx-postponed")
    days = s.scalars(select(MatchSchedule.scheduled_at).filter_by(match_id=m.id).order_by(MatchSchedule.seq)).all()
    assert (m.status, [d.day for d in days]) == ("scheduled", [1, 2])
    assert entity_for(s, "match", "bp:fx-cancelled") is None


def test_equipo_por_decidir_con_y_sin_origen(s):
    slots = {x.side: x for x in s.scalars(select(MatchSlot).filter_by(match_id=match_of(s, "bp:fx-tbd-origin").id))}
    assert (slots[1].origin_match_id, slots[1].origin_outcome) == (entity_for(s, "match", "bp:fx-main"), "winner")
    assert slots[2].origin_outcome == "loser"
    none = s.scalars(select(MatchSlot).filter_by(match_id=match_of(s, "bp:fx-tbd-none").id)).all()
    assert all(x.franchise_id is None and x.origin_match_id is None for x in none) and len(none) == 2


def test_en_vivo_sin_marcador(s):
    m = match_of(s, "bp:fx-live")
    assert (m.status, m.maps_won_1, m.maps_won_2, m.live_score_1) == ("live", 0, 0, None)


def test_mapa_repetido_y_mapas_no_jugados(s):
    maps = s.scalars(select(MatchMap).filter_by(match_id=match_of(s, "bp:fx-main").id).order_by(MatchMap.position)).all()
    assert [m.position for m in maps] == [1, 2, 3, 4, 5]
    assert (maps[1].played, maps[1].score_1) == (True, 6)
    assert [m.played for m in maps[3:]] == [False, False]


def test_fase_y_modo_desconocidos(s):
    m = match_of(s, "bp:fx-unknown")
    assert m.phase is None
    stats = s.scalars(select(PlayerMapStats).join(MatchMap).filter(MatchMap.match_id == m.id)).one()
    assert (stats.kills, stats.zone_captures, stats.hill_time) == (22, None, None)


def test_valor_imposible_y_correccion_tras_finalizar(s):
    main = match_of(s, "bp:fx-main")
    map2 = one(s, MatchMap, match_id=main.id, position=2)
    a1 = player(s, "bp:fx-A1").id
    stats = one(s, PlayerMapStats, map_id=map2.id, player_id=a1)
    assert (stats.kills, stats.deaths, stats.plants) == (None, 5, 1)
    map1 = one(s, MatchMap, match_id=main.id, position=1)
    assert (map1.score_2, map1.corrected_fields) == (185, ["score_2"])


def test_estadisticas_pendientes_jugador_sin_ninguna_estadistica(s):
    map3 = one(s, MatchMap, match_id=match_of(s, "bp:fx-main").id, position=3)
    stats = one(s, PlayerMapStats, map_id=map3.id, player_id=player(s, "bp:fx-B1").id)
    assert all(getattr(stats, f) is None for f in ("kills", "deaths", "kd", "damage", "assists", "zone_captures", "overloads"))


def test_suplente_y_agente_libre(s):
    map1 = one(s, MatchMap, match_id=match_of(s, "bp:fx-main").id, position=1)
    sub = one(s, PlayerMapStats, map_id=map1.id, player_id=player(s, "bp:fx-Sub").id)
    free = one(s, PlayerMapStats, map_id=map1.id, player_id=player(s, "bp:fx-Free").id)
    assert (sub.is_substitute, free.is_substitute) == (True, False)  # el 15-01 aún estaba en el roster
    from datetime import UTC, datetime
    assert is_free_agent(s, player(s, "bp:fx-Free").id, now=datetime(2026, 9, 22, tzinfo=UTC))


def test_solo_anio_solo_edad_y_retirado(s):
    assert (player(s, "bp:fx-Year").birth_year, player(s, "bp:fx-Year").birth_year_is_approx) == (2003, False)
    assert (player(s, "bp:fx-Age").birth_year, player(s, "bp:fx-Age").birth_year_is_approx) == (2005, True)
    retired = player(s, "bp:fx-Retired")
    assert retired.retired is True
    assert s.scalars(select(PlayerGamertag.gamertag).filter_by(player_id=retired.id)).all() == ["[FICTICIO] Nombre De Antes"]


def test_mismo_gamertag_dos_personas_y_html_literal(s):
    assert player(s, "bp:fx-Twin1").id != player(s, "wiki:Twin_2").id
    assert player(s, "bp:fx-Html").current_gamertag == '[FICTICIO] <img src=x onerror="alert(1)">'


def test_identidades_sin_logo_sin_color_y_logo_no_valido(s):
    def ids(ref):
        return s.scalars(select(Identity).filter_by(franchise_id=entity_for(s, "franchise", ref)).order_by(Identity.valid_from)).all()
    assert (ids("bp:fx-NoLogo")[0].logo_url, ids("bp:fx-NoLogo")[0].primary_color) == (None, "#f5d90a")
    assert (ids("bp:fx-NoColor")[0].logo_url, ids("bp:fx-NoColor")[0].primary_color) == (None, None)
    old, new = ids("bp:fx-Old")
    assert old.logo_url is not None and new.logo_url is None
    assert ids("bp:fx-B")[0].logo_url is None  # javascript: descartado


def test_empate_en_la_tabla(s):
    rows = s.scalars(select(Standing).where(Standing.position == 13)).all()
    assert len(rows) == 2 and {r.points for r in rows} == {0}


def test_campeonato_sin_fecha_incompleto_y_dq(s):
    champ = one(s, Championship, year=2014)
    assert champ.final_date is None
    rows = {p.place: p for p in s.scalars(select(Placement).filter_by(championship_id=champ.id))}
    assert identity_name(s, rows["1"].identity_id) == "[FICTICIO] Nombre Antiguo"  # coincide por nombre
    assert identity_name(s, rows["DQ"].identity_id) == "[FICTICIO] Equipo A"  # vigente el 31-12-2014 (la más antigua)
    assert (rows["DQ"].is_dq, rows["DQ"].prize_usd) == (True, None)


def test_curacion_de_ejemplo(s):
    assert (player(s, "bp:fx-A1").role, player(s, "bp:fx-A2").role, player(s, "bp:fx-A3").role) == ("SMG", "AR", None)
    assert player(s, "bp:fx-MergeA").id == player(s, "wiki:Merge_B").id
    assert player(s, "bp:fx-SplitA").id != player(s, "wiki:Split_B").id
    removed = player(s, "bp:fx-Removed")
    assert (removed.real_name, removed.country, removed.birth_date, removed.personal_data_removed) == (None, None, None, True)


def test_la_franquicia_que_sale_se_borra_al_cambiar_de_temporada_y_el_historial_queda(loaded):
    session, _ = loaded
    leaving = entity_for(session, "franchise", "bp:fx-Leaving")
    assert session.get(Franchise, leaving) is not None
    report = ingest_records(session, [
        {"kind": "season", "source": "bp", "source_id": "fx-2027", "observed_at": "2026-12-01T00:00:00Z",
         "year": 2027, "fictional": True},
        {"kind": "event", "source": "bp", "source_id": "fx-2027-ev", "observed_at": "2026-12-01T00:00:00Z",
         "season_year": 2027, "name": "[FICTICIO] Primer evento 2027", "fictional": True},
        {"kind": "match", "source": "bp", "source_id": "fx-2027-m", "observed_at": "2026-12-05T00:00:00Z",
         "event_ref": "bp:fx-2027-ev", "best_of": 5, "status": "live", "fictional": True},
    ])
    session.flush()
    assert report.rejected == []
    assert current_season(session).year == 2027
    assert entity_for(session, "franchise", "bp:fx-Leaving") is None
    assert session.scalar(select(func.count()).select_from(Championship)) == 6
    assert player(session, "wiki:Simp") is not None  # figura en el historial
    session.rollback()  # este caso no se guarda
