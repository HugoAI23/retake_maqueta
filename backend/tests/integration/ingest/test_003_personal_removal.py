"""T-045 · La retirada de datos personales es permanente (spec 003, RF-60; RF-78 de la 002).

Ni un instante: los datos personales de un jugador retirado no se guardan en ninguna
observación ni en el jugador, aunque la ingesta llegue antes de aplicar la curación o
una fuente nueva se enlace al jugador.
"""

from sqlalchemy import func, select

from app.curation.loader import parse_curation
from app.db.models import Observation, Player
from app.ingest.resolvers import PERSONAL_FIELDS
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec

REMOVAL = "personal_data_removals: [ {player: 'bp:p1', requested_on: 2026-09-01} ]"


def personal_observations(session) -> int:
    return session.scalar(select(func.count()).select_from(Observation).where(Observation.field.in_(PERSONAL_FIELDS)))


def player_of(session, ref):
    session.expire_all()
    return session.get(Player, entity_for(session, "player", ref))


def test_un_jugador_nuevo_con_retirada_en_la_curacion_no_guarda_datos_personales(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", real_name="Nombre", country="Mexico", birth_year=2000)],
           curation=parse_curation(REMOVAL))
    player = player_of(session, "bp:p1")
    assert (player.real_name, player.country, player.birth_year, player.personal_data_removed) == (None, None, None, True)
    assert personal_observations(session) == 0


def test_reingerir_un_jugador_retirado_no_guarda_ninguna_observacion_personal(session, ingest):
    curation = parse_curation(REMOVAL)
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno")], curation=curation)
    ingest([rec("player", "p1", hours=1, gamertag="[FICTICIO] Uno", real_name="Nombre", age=25)], curation=curation)
    player = player_of(session, "bp:p1")
    assert (player.real_name, player.birth_year) == (None, None)
    assert personal_observations(session) == 0


def test_una_fuente_nueva_enlazada_a_un_jugador_retirado_no_aporta_datos_personales(session, ingest):
    curation = parse_curation(REMOVAL)
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno")], curation=curation)
    ingest([rec("player", "Uno", source="wiki", hours=1, gamertag="[FICTICIO] Uno", same_as=["bp:p1"],
                real_name="Nombre", country="Mexico", birth_date="2000-01-01")], curation=curation)
    player = player_of(session, "wiki:Uno")
    assert player.id == entity_for(session, "player", "bp:p1")
    assert (player.real_name, player.country, player.birth_date) == (None, None, None)
    assert personal_observations(session) == 0


def test_la_retirada_sigue_vigente_aunque_la_curacion_ya_no_la_liste(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno")], curation=parse_curation(REMOVAL))
    ingest([rec("player", "p1", hours=1, gamertag="[FICTICIO] Uno", real_name="Nombre")])
    assert player_of(session, "bp:p1").real_name is None
    assert personal_observations(session) == 0
