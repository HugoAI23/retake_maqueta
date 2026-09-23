"""T-033 y T-038 · Jugadores, rosters y estado calculado."""

from datetime import UTC, datetime

from sqlalchemy import func, select

from app.db.models import Player, PlayerGamertag, RosterMembership
from app.db.queries import championship_ids_for_player, is_current_season_player, is_free_agent
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec, season_and_event, team

NOW = datetime(2026, 3, 1, tzinfo=UTC)


def test_gamertags_actual_y_anteriores_en_orden(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Actual", previous_gamertags=["[FICTICIO] Primero", "[FICTICIO] Segundo"], retired=True)])
    player = session.scalars(select(Player)).one()
    assert player.current_gamertag == "[FICTICIO] Actual"
    assert player.retired is True
    tags = session.scalars(select(PlayerGamertag.gamertag).order_by(PlayerGamertag.position)).all()
    assert tags == ["[FICTICIO] Primero", "[FICTICIO] Segundo"]


def test_datos_personales_de_las_fuentes_y_pais_unico(session, ingest):
    ingest([rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno", country="Spain", real_name="Nombre Wiki"),
            rec("player", "p1", gamertag="[FICTICIO] Uno", country="Mexico", same_as=["wiki:Uno"])])
    player = session.scalars(select(Player)).one()
    assert (player.country, player.real_name) == ("Mexico", "Nombre Wiki")


def test_una_edad_publicada_sin_fecha_da_un_anio_aproximado(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", age=24)])  # observado en 2026
    player = session.scalars(select(Player)).one()
    assert (player.birth_year, player.birth_year_is_approx) == (2002, True)


def test_la_fecha_completa_manda_sobre_el_anio_y_la_edad(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", birth_date="2001-04-02", birth_year=1999, age=30)])
    player = session.scalars(select(Player)).one()
    assert str(player.birth_date) == "2001-04-02"
    assert player.birth_year_is_approx is False


def _world(ingest, extra=()):
    ingest([
        *season_and_event(),
        *team("t1", "[FICTICIO] Equipo"),
        rec("player", "p1", gamertag="[FICTICIO] Titular"),
        rec("player", "p2", gamertag="[FICTICIO] Suplente"),
        rec("roster", "r1", season_year=2026, franchise_ref="bp:t1", player_ref="bp:p1", **{"from": "2025-11-01T00:00:00Z"}),
        rec("match", "m1", event_ref="bp:ev1", best_of=5, status="finished", scheduled_at="2026-01-11T18:00:00Z"),
        rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played", score=[250, 1], winner_side=1),
        rec("player_map_stats", "s1", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=20),
        rec("player_map_stats", "s2", map_ref="bp:mp1", player_ref="bp:p2", franchise_ref="bp:t1", kills=15),
        *extra,
    ])


def test_el_roster_solo_sale_de_registros_de_roster(session, ingest):
    _world(ingest)
    rosters = session.scalars(select(RosterMembership)).all()
    assert [r.player_id for r in rosters] == [entity_for(session, "player", "bp:p1")]


def test_jugador_de_la_temporada_por_roster_o_por_partido(session, ingest):
    _world(ingest, extra=[rec("player", "p3", gamertag="[FICTICIO] Sin nada")])
    assert is_current_season_player(session, entity_for(session, "player", "bp:p1"))
    assert is_current_season_player(session, entity_for(session, "player", "bp:p2"))
    assert not is_current_season_player(session, entity_for(session, "player", "bp:p3"))


def test_agente_libre_es_de_la_temporada_y_no_tiene_roster_abierto(session, ingest):
    _world(ingest)
    assert not is_free_agent(session, entity_for(session, "player", "bp:p1"), now=NOW)
    assert is_free_agent(session, entity_for(session, "player", "bp:p2"), now=NOW)
    ingest([rec("roster", "r1", hours=1, season_year=2026, franchise_ref="bp:t1", player_ref="bp:p1",
                **{"from": "2025-11-01T00:00:00Z", "to": "2026-02-01T00:00:00Z"})])
    assert is_free_agent(session, entity_for(session, "player", "bp:p1"), now=NOW)


def test_campeonatos_de_un_jugador(session, ingest):
    ingest([
        *team("F", "[FICTICIO] Campeón", source="wiki"),
        rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno"),
        rec("championship", "C2020", source="wiki", year=2020, completed=True),
        rec("championship", "C2026", source="wiki", year=2026, completed=False),
        rec("placement", "P2020", source="wiki", championship_ref="wiki:C2020", franchise_ref="wiki:F", place="1",
            roster=[{"player_ref": "wiki:Uno"}]),
        rec("placement", "P2026", source="wiki", championship_ref="wiki:C2026", franchise_ref="wiki:F", place="1",
            roster=[{"player_ref": "wiki:Uno"}]),
    ])
    ids = championship_ids_for_player(session, entity_for(session, "player", "wiki:Uno"))
    assert ids == [entity_for(session, "championship", "wiki:C2020")]
    assert session.scalar(select(func.count()).select_from(Player)) == 1
