"""T-034, T-035 y T-036 · Partidos, mapas, estadísticas y tabla de posiciones."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.db.models import Match, MatchMap, MatchSchedule, MatchSlot, PlayerMapStats, Season, Standing
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import T0, rec, season_and_event, team


def base():
    return [*season_and_event(), *team("t1", "[FICTICIO] Uno"), *team("t2", "[FICTICIO] Dos")]


def match(source_id="m1", hours=0, **fields):
    fields.setdefault("best_of", 5)
    return rec("match", source_id, hours=hours, event_ref="bp:ev1", **fields)


def get_match(session):
    session.expire_all()
    return session.scalars(select(Match)).one()


def test_pasar_a_en_vivo_fija_el_inicio_del_partido_y_de_la_temporada_con_0_0(session, ingest):
    ingest([*base(), match(status="scheduled", scheduled_at="2026-01-11T18:00:00Z")])
    ingest([match(hours=1, status="live")])
    m = get_match(session)
    assert m.status == "live"
    assert m.went_live_at == datetime(2026, 1, 10, 13, 0, tzinfo=UTC)
    assert (m.maps_won_1, m.maps_won_2) == (0, 0)
    assert session.scalars(select(Season)).one().started_at == m.went_live_at


def test_se_conserva_el_ultimo_marcador_conocido(session, ingest):
    ingest([*base(), match(status="live", maps_won=[1, 0], live_map={"mode": "Hardpoint", "score": [100, 80]})])
    ingest([match(hours=1, status="live")])
    m = get_match(session)
    assert (m.maps_won_1, m.live_mode, m.live_score_1, m.live_score_2) == (1, "Hardpoint", 100, 80)


def test_un_partido_finalizado_no_vuelve_a_en_vivo(session, ingest):
    ingest([*base(), match(status="finished", maps_won=[3, 1], winner_side=1)])
    ingest([match(hours=1, status="live")])
    m = get_match(session)
    assert (m.status, m.winner_side, m.live_mode) == ("finished", 1, None)


def test_un_aplazamiento_guarda_todos_los_horarios(session, ingest):
    ingest([*base(), match(status="scheduled", scheduled_at="2026-01-11T18:00:00Z")])
    ingest([match(hours=1, status="postponed", scheduled_at="2026-01-12T18:00:00Z")])
    assert get_match(session).status == "scheduled"
    schedule = session.scalars(select(MatchSchedule.scheduled_at).order_by(MatchSchedule.seq)).all()
    assert [s.day for s in schedule] == [11, 12]


def test_forfeit_finalizado_sin_mapas_y_sin_iniciar_la_temporada(session, ingest):
    ingest([*base(), match(status="forfeit", maps_won=[3, 0], winner_side=1)])
    m = get_match(session)
    assert (m.status, m.maps_won_1, m.winner_side, m.went_live_at) == ("finished", 3, 1, None)
    assert session.scalars(select(Season)).one().started_at is None


def test_un_partido_cancelado_se_borra_pero_la_temporada_sigue_iniciada(session, ingest):
    ingest([*base(), match(status="live")])
    ingest([match(hours=1, status="cancelled")])
    assert session.scalars(select(Match)).all() == []
    assert session.scalars(select(Season)).one().started_at is not None


def test_fase_reconocida_y_fase_desconocida(session, ingest):
    ingest([*base(), match("m1", phase="Winners Bracket"), match("m2", phase="play-in")])
    phases = {m.phase for m in session.scalars(select(Match))}
    assert phases == {"winners_bracket", None}


def test_equipos_conocidos_y_por_decidir(session, ingest):
    ingest([*base(),
            match("m1", slots=[{"franchise_ref": "bp:t1"}, {"franchise_ref": "bp:t2"}]),
            match("m2", slots=[{"origin": {"match_ref": "bp:m1", "outcome": "winner"}}, None])])
    m2 = entity_for(session, "match", "bp:m2")
    slots = {s.side: s for s in session.scalars(select(MatchSlot).where(MatchSlot.match_id == m2))}
    assert slots[1].origin_match_id == entity_for(session, "match", "bp:m1")
    assert slots[1].origin_outcome == "winner"
    assert (slots[2].franchise_id, slots[2].origin_match_id) == (None, None)


def test_mapas_ganados_imposibles_y_ganador_no_valido_quedan_ausentes(session, ingest):
    ingest([*base(), match(status="finished", maps_won=[4, 1], winner_side=3)])
    m = get_match(session)
    assert (m.maps_won_1, m.maps_won_2, m.winner_side) == (None, 1, None)


def maps_base():
    return [*base(), match(status="finished", maps_won=[3, 1], winner_side=1),
            rec("player", "p1", gamertag="[FICTICIO] Jugador")]


def test_mapa_repetido_solo_cuenta_la_version_con_ganador(session, ingest):
    ingest([*maps_base(),
            rec("match_map", "old", match_ref="bp:m1", position=2, mode="Search & Destroy", status="voided"),
            rec("match_map", "replay", match_ref="bp:m1", position=2, mode="Search & Destroy", status="played",
                score=[6, 4], winner_side=1)])
    maps = session.scalars(select(MatchMap)).all()
    assert len(maps) == 1 and maps[0].played and maps[0].score_1 == 6


def test_mapa_no_jugado_se_guarda_sin_marcador(session, ingest):
    ingest([*maps_base(),
            rec("match_map", "mp5", match_ref="bp:m1", position=5, mode="Hardpoint", map_name="Vault", status="not_played")])
    game_map = session.scalars(select(MatchMap)).one()
    assert (game_map.played, game_map.map_name, game_map.score_1, game_map.winner_side) == (False, "Vault", None, None)


def test_estadisticas_por_modo_y_kd_publicado(session, ingest):
    ingest([*maps_base(),
            rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played", score=[250, 1], winner_side=1),
            rec("match_map", "mp2", match_ref="bp:m1", position=2, mode="Control", status="played", score=[3, 1], winner_side=1),
            rec("player_map_stats", "a", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1",
                kills=10, deaths=10, kd=1.5, hill_time=90, first_bloods=2),
            rec("player_map_stats", "b", map_ref="bp:mp2", player_ref="bp:p1", franchise_ref="bp:t1",
                kills=8, zone_captures=3, hill_time=10)])
    hp, control = sorted(session.scalars(select(PlayerMapStats)), key=lambda s: s.kills, reverse=True)
    assert hp.kd == Decimal("1.5")  # tal como se publica, no 10/10
    assert (hp.hill_time, hp.first_bloods) == (90, None)
    assert (control.kills, control.zone_captures, control.hill_time) == (8, None, None)


def test_kd_calculado_si_ninguna_fuente_lo_publica(session, ingest):
    """T-091 (C-12): kills ÷ deaths con 2 decimales; con 0 deaths, K/D = kills; si falta alguno, ausente."""
    ingest([*maps_base(),
            rec("player", "p2", gamertag="[FICTICIO] Dos"), rec("player", "p3", gamertag="[FICTICIO] Tres"),
            rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played", score=[250, 1], winner_side=1),
            rec("player_map_stats", "a", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=20, deaths=17),
            rec("player_map_stats", "b", map_ref="bp:mp1", player_ref="bp:p2", franchise_ref="bp:t1", kills=6, deaths=0),
            rec("player_map_stats", "c", map_ref="bp:mp1", player_ref="bp:p3", franchise_ref="bp:t1", deaths=9)])
    kd = {s.player_id: s.kd for s in session.scalars(select(PlayerMapStats))}
    assert kd[entity_for(session, "player", "bp:p1")] == Decimal("1.18")
    assert kd[entity_for(session, "player", "bp:p2")] == Decimal("6")
    assert kd[entity_for(session, "player", "bp:p3")] is None


def test_estadisticas_en_el_equipo_del_partido_y_suplente_marcado(session, ingest):
    ingest([*maps_base(),
            rec("player", "p2", gamertag="[FICTICIO] Suplente"),
            rec("roster", "r1", season_year=2026, franchise_ref="bp:t1", player_ref="bp:p1"),
            rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played", score=[250, 1], winner_side=1),
            rec("player_map_stats", "a", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=10),
            rec("player_map_stats", "b", map_ref="bp:mp1", player_ref="bp:p2", franchise_ref="bp:t1", kills=9)])
    by_player = {s.player_id: s for s in session.scalars(select(PlayerMapStats))}
    regular = by_player[entity_for(session, "player", "bp:p1")]
    substitute = by_player[entity_for(session, "player", "bp:p2")]
    assert regular.franchise_id == substitute.franchise_id == entity_for(session, "franchise", "bp:t1")
    assert (regular.is_substitute, substitute.is_substitute) == (False, True)


def test_tabla_con_prioridad_de_la_web_oficial_y_posiciones_compartidas(session, ingest):
    ingest([*base(),
            rec("franchise", "T1", source="cdl", same_as=["bp:t1"]),
            rec("standing", "st1", season_year=2026, franchise_ref="bp:t1", position=1, points=200),
            rec("standing", "ST1", source="cdl", season_year=2026, franchise_ref="cdl:T1", position=2, points=210),
            rec("standing", "st2", season_year=2026, franchise_ref="bp:t2", position=2, points=210)])
    rows = {s.franchise_id: (s.position, s.points) for s in session.scalars(select(Standing))}
    assert rows[entity_for(session, "franchise", "bp:t1")] == (2, 210)
    assert rows[entity_for(session, "franchise", "bp:t2")] == (2, 210)
    assert len(rows) == 2


def test_t0_helper_es_utc():
    assert T0.tzinfo is UTC


def test_si_se_cancela_el_partido_de_origen_el_lado_queda_sin_origen(session, ingest):
    ingest([*base(),
            match("m1", status="scheduled"),
            match("m2", slots=[{"origin": {"match_ref": "bp:m1", "outcome": "winner"}}, None])])
    ingest([match("m1", hours=1, status="cancelled")])
    m2 = entity_for(session, "match", "bp:m2")
    slot = session.scalars(select(MatchSlot).where(MatchSlot.match_id == m2, MatchSlot.side == 1)).one()
    assert (slot.origin_match_id, slot.origin_outcome) == (None, None)
