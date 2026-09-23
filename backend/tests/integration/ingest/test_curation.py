"""T-039 · Aplicación de la curación (RF-26, RF-27, RF-76, RF-78, RF-131, RF-133)."""

import pytest
from sqlalchemy import func, select

from app.curation.loader import CurationError, parse_curation
from app.curation.overlay import apply_curation
from app.db.models import Observation, Player, PlayerMapStats
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec, season_and_event, team


def apply(session, text):
    apply_curation(session, parse_curation(text))
    session.commit()
    session.expire_all()


def player_of(session, ref):
    return session.get(Player, entity_for(session, "player", ref))


def test_roles_se_asignan_cambian_sin_historial_y_vuelven_a_sin_rol(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno")])
    apply(session, "roles: [ {player: 'bp:p1', role: SMG, reason: 'x'} ]")
    assert player_of(session, "bp:p1").role == "SMG"
    apply(session, "roles: [ {player: 'bp:p1', role: AR, reason: 'cambio de rol'} ]")
    assert player_of(session, "bp:p1").role == "AR"
    apply(session, "roles: []")
    assert player_of(session, "bp:p1").role is None


def test_una_union_de_la_curacion_junta_dos_jugadores(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno"), rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno")])
    apply(session, "player_merges: [ {players: ['bp:p1', 'wiki:Uno'], reason: 'misma persona'} ]")
    assert session.scalar(select(func.count()).select_from(Player)) == 1


def test_una_separacion_de_la_curacion_divide_y_mueve_las_estadisticas(session, ingest):
    ingest([
        *season_and_event(), *team("t1", "[FICTICIO] Equipo"),
        rec("match", "m1", event_ref="bp:ev1", best_of=5, status="finished"),
        rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played", score=[250, 1], winner_side=1),
        rec("player", "p1", gamertag="[FICTICIO] Uno"),
        rec("player", "Otro", source="wiki", gamertag="[FICTICIO] Otro", same_as=["bp:p1"]),
        rec("player_map_stats", "s", source="wiki", map_ref="bp:mp1", player_ref="wiki:Otro", franchise_ref="bp:t1", kills=7),
    ])
    assert session.scalar(select(func.count()).select_from(Player)) == 1
    apply(session, "player_splits: [ {players: ['bp:p1', 'wiki:Otro'], reason: 'personas distintas'} ]")
    assert session.scalar(select(func.count()).select_from(Player)) == 2
    other = entity_for(session, "player", "wiki:Otro")
    assert other != entity_for(session, "player", "bp:p1")
    assert session.scalars(select(PlayerMapStats)).one().player_id == other
    assert player_of(session, "wiki:Otro").current_gamertag == "[FICTICIO] Otro"


def test_unir_y_separar_lo_mismo_es_un_error_y_no_cambia_nada(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno"), rec("player", "p2", gamertag="[FICTICIO] Dos")])
    with pytest.raises(CurationError):
        apply_curation(session, parse_curation(
            "player_merges: [ {players: ['bp:p1', 'bp:p2'], reason: 'x'} ]\n"
            "player_splits: [ {players: ['bp:p1', 'bp:p2'], reason: 'y'} ]"))
    session.rollback()
    assert session.scalar(select(func.count()).select_from(Player)) == 2


def test_una_referencia_desconocida_en_la_curacion_es_un_error(session):
    with pytest.raises(CurationError, match="bp:fantasma"):
        apply_curation(session, parse_curation("roles: [ {player: 'bp:fantasma', role: SMG, reason: 'x'} ]"))


def test_retirar_datos_personales_los_borra_y_no_vuelven(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", real_name="Nombre", country="Mexico", birth_year=2000)])
    apply(session, "personal_data_removals: [ {player: 'bp:p1', requested_on: 2026-09-01} ]")
    player = player_of(session, "bp:p1")
    assert (player.real_name, player.country, player.birth_year, player.personal_data_removed) == (None, None, None, True)
    assert session.scalar(select(func.count()).select_from(Observation).where(Observation.field == "real_name")) == 0
    ingest([rec("player", "p1", hours=1, gamertag="[FICTICIO] Uno", real_name="Nombre otra vez")])
    session.expire_all()
    assert player_of(session, "bp:p1").real_name is None


def test_aplicar_la_curacion_dos_veces_da_el_mismo_resultado(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno"), rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno")])
    text = ("roles: [ {player: 'bp:p1', role: SMG, reason: 'x'} ]\n"
            "player_merges: [ {players: ['bp:p1', 'wiki:Uno'], reason: 'y'} ]")
    apply(session, text)
    first = [(p.id, p.role) for p in session.scalars(select(Player))]
    apply(session, text)
    assert [(p.id, p.role) for p in session.scalars(select(Player))] == first


def test_la_ingesta_respeta_las_separaciones_de_la_curacion(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno"), rec("player", "Otro", source="wiki", gamertag="[FICTICIO] Otro")])
    curation = parse_curation("player_splits: [ {players: ['bp:p1', 'wiki:Otro'], reason: 'distintos'} ]")
    ingest([rec("player", "Otro", source="wiki", hours=1, gamertag="[FICTICIO] Otro", same_as=["bp:p1"])], curation=curation)
    assert session.scalar(select(func.count()).select_from(Player)) == 2
