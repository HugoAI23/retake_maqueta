"""T-030 y T-031 · Núcleo de la ingesta y valor resuelto (plan §3.3)."""

from decimal import Decimal

from sqlalchemy import func, select

from app.db.models import ExternalRef, Observation, Player, PlayerMapStats
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec, season_and_event, team


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_alta_de_un_jugador(session, ingest):
    report = ingest([rec("player", "p1", gamertag="[FICTICIO] Uno")])
    assert report.accepted == 1 and report.rejected == []
    player = session.scalars(select(Player)).one()
    assert player.current_gamertag == "[FICTICIO] Uno"
    assert entity_for(session, "player", "bp:p1") == player.id


def test_un_enlace_same_as_une_dos_referencias_sin_perder_observaciones(session, ingest):
    ingest([
        rec("player", "p1", gamertag="[FICTICIO] Uno"),
        rec("player", "Uno_Page", source="wiki", gamertag="[FICTICIO] Uno", country="Mexico", same_as=["bp:p1"]),
    ])
    assert count(session, Player) == 1
    assert entity_for(session, "player", "bp:p1") == entity_for(session, "player", "wiki:Uno_Page")
    assert count(session, Observation) == 3  # gamertag (bp), gamertag y country (wiki)


def test_mismo_gamertag_sin_enlace_son_dos_jugadores(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Igual"), rec("player", "p2", gamertag="[FICTICIO] Igual")])
    assert count(session, Player) == 2


def test_una_union_posterior_conserva_el_identificador_mas_antiguo_y_mueve_sus_datos(session, ingest):
    ingest([
        *season_and_event(),
        *team("t1", "[FICTICIO] Equipo"),
        rec("match", "m1", event_ref="bp:ev1", best_of=5, status="finished", scheduled_at="2026-01-11T18:00:00Z"),
        rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played", score=[250, 200], winner_side=1),
        rec("player", "p1", gamertag="[FICTICIO] Uno"),
        rec("player", "Uno_Page", source="wiki", gamertag="[FICTICIO] Uno Wiki"),
        rec("player_map_stats", "st1", source="wiki", map_ref="bp:mp1", player_ref="wiki:Uno_Page", franchise_ref="bp:t1", kills=20),
    ])
    oldest = entity_for(session, "player", "bp:p1")
    ingest([rec("player", "Uno_Page", source="wiki", hours=1, gamertag="[FICTICIO] Uno Wiki", same_as=["bp:p1"])])
    assert count(session, Player) == 1
    assert entity_for(session, "player", "wiki:Uno_Page") == oldest
    assert session.scalars(select(PlayerMapStats)).one().player_id == oldest


def test_prioridad_y_un_campo_omitido_no_borra_el_valor(session, ingest):
    ingest([rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno", country="Spain"),
            rec("player", "p1", gamertag="[FICTICIO] Uno", country="Mexico", same_as=["wiki:Uno"])])
    assert session.scalars(select(Player)).one().country == "Mexico"
    ingest([rec("player", "p1", hours=2, gamertag="[FICTICIO] Uno")])  # sin country
    session.expire_all()
    assert session.scalars(select(Player)).one().country == "Mexico"


def _finished_map(extra_stats=None):
    return [
        *season_and_event(),
        *team("t1", "[FICTICIO] Equipo"),
        rec("player", "p1", gamertag="[FICTICIO] Uno"),
        rec("match", "m1", event_ref="bp:ev1", best_of=5, status="finished", scheduled_at="2026-01-11T18:00:00Z",
            maps_won=[3, 1], winner_side=1),
        rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played",
            score=[250, 200], winner_side=1),
    ]


def test_un_valor_imposible_se_descarta_sin_perder_el_resto(session, ingest):
    ingest([*_finished_map(),
            rec("player_map_stats", "st1", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1",
                kills=-5, deaths=18, damage=0)])
    stats = session.scalars(select(PlayerMapStats)).one()
    assert stats.kills is None
    assert stats.deaths == 18
    assert stats.damage == 0  # 0 es un valor, no una ausencia
    assert stats.assists is None  # no publicado
    invalid = session.scalars(select(Observation).where(Observation.field == "kills")).one()
    assert invalid.is_valid is False


def test_un_cambio_en_un_partido_finalizado_se_marca_como_correccion(session, ingest):
    ingest(_finished_map())
    ingest([rec("match_map", "mp1", hours=1, match_ref="bp:m1", position=1, mode="Hardpoint", status="played",
                score=[250, 210], winner_side=1)])
    from app.db.models import MatchMap

    game_map = session.scalars(select(MatchMap)).one()
    assert game_map.score_2 == 210
    assert game_map.corrected_fields == ["score_2"]


def test_la_primera_llegada_de_un_dato_no_es_una_correccion(session, ingest):
    ingest([*_finished_map(),
            rec("player_map_stats", "st1", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=20)])
    assert session.scalars(select(PlayerMapStats)).one().corrected_fields == []


def test_un_dato_no_valido_y_luego_valido_en_un_partido_finalizado_es_una_correccion(session, ingest):
    ingest([*_finished_map(),
            rec("player_map_stats", "st1", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=-1)])
    ingest([rec("player_map_stats", "st1", hours=1, map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=20)])
    stats = session.scalars(select(PlayerMapStats)).one()
    assert stats.kills == 20
    assert stats.corrected_fields == ["kills"]


def test_corregir_kills_corrige_tambien_el_kd_calculado(session, ingest):
    """T-091 (C-12): el K/D calculado sigue a kills y deaths, también en sus correcciones."""
    ingest([*_finished_map(),
            rec("player_map_stats", "st1", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=20, deaths=10)])
    ingest([rec("player_map_stats", "st1", hours=1, map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1",
                kills=25, deaths=10)])
    stats = session.scalars(select(PlayerMapStats)).one()
    assert stats.kd == Decimal("2.5")
    assert stats.corrected_fields == ["kills", "kd"]


def test_un_registro_con_una_referencia_desconocida_se_rechaza_sin_afectar_a_los_demas(session, ingest):
    report = ingest([
        rec("roster", "r1", season_year=2026, franchise_ref="bp:nope", player_ref="bp:nope"),
        rec("player", "p1", gamertag="[FICTICIO] Uno"),
    ])
    assert report.accepted == 1
    assert len(report.rejected) == 1
    assert report.rejected[0].index == 0
    assert "bp:nope" in report.rejected[0].reason
    assert count(session, Player) == 1


def test_un_registro_mal_formado_se_rechaza_con_su_motivo(ingest):
    report = ingest([{"kind": "season", "source": "bp"}])
    assert report.accepted == 0
    assert "Registro mal formado" in report.rejected[0].reason


def test_una_observacion_mas_antigua_que_la_guardada_se_ignora(session, ingest):
    ingest([rec("player", "p1", hours=5, gamertag="[FICTICIO] Nuevo")])
    ingest([rec("player", "p1", hours=1, gamertag="[FICTICIO] Viejo")])
    assert session.scalars(select(Player)).one().current_gamertag == "[FICTICIO] Nuevo"


def test_las_referencias_de_datos_ficticios_quedan_marcadas(session, ingest):
    ingest([{**rec("player", "p1", gamertag="[FICTICIO] Uno"), "fictional": True}])
    assert session.scalars(select(ExternalRef)).one().fictional is True
