"""T-037 · Dato ilegible frente a valor imposible (spec 003: RF-48, RF-49; plan D-8)."""

from sqlalchemy import select

from app.db.models import Observation, Player, PlayerMapStats
from tests.integration.ingest.helpers import rec

BP, WIKI = "bp:p1", "wiki:P1"


def player(source="bp", source_id="p1", hours=0, **fields):
    fields.setdefault("gamertag", "[FICTICIO] Jugador")
    return rec("player", source_id, source=source, hours=hours, **fields)


def get_player(session):
    session.expire_all()
    return session.scalars(select(Player)).one()


def test_un_dato_ilegible_cede_el_turno_a_la_siguiente_fuente(session, ingest):
    ingest([player(country="[FICTICIO] Canadá"),
            player(source="wiki", source_id="P1", same_as=[BP], country="[FICTICIO] México")])
    assert get_player(session).country == "[FICTICIO] Canadá"  # manda BreakingPoint
    ingest([player(hours=1, unreadable=["country"])])
    assert get_player(session).country == "[FICTICIO] México"  # RF-48


def test_si_ninguna_fuente_lo_publica_legible_se_conserva_el_valor_registrado(session, ingest):
    ingest([player(country="[FICTICIO] Canadá")])
    ingest([player(hours=1, unreadable=["country"])])
    assert get_player(session).country == "[FICTICIO] Canadá"  # RF-49
    obs = session.scalars(select(Observation).where(Observation.field == "country")).one()
    assert (obs.is_valid, obs.invalid_reason) == (False, "unreadable")


def test_un_dato_ilegible_que_nunca_llego_queda_ausente(session, ingest):
    ingest([player(unreadable=["country"])])
    assert get_player(session).country is None


def test_un_valor_imposible_sigue_pasando_a_ausente(session, ingest):
    from tests.integration.ingest.test_matches import base, match
    ingest([*base(), match(status="finished", maps_won=[3, 1], winner_side=1),
            rec("match_map", "m1-1", match_ref="bp:m1", position=1, mode="Hardpoint", map_name="Colossus",
                status="played", score=[250, 200], winner_side=1),
            player(), rec("player_map_stats", "m1-1-p1", map_ref="bp:m1-1", player_ref=BP, franchise_ref="bp:t1",
                          kills=20)])
    ingest([rec("player_map_stats", "m1-1-p1", hours=1, map_ref="bp:m1-1", player_ref=BP, franchise_ref="bp:t1",
                kills=-3)])
    session.expire_all()
    assert session.scalars(select(PlayerMapStats)).one().kills is None  # RF-100 de la 002
    obs = session.scalars(select(Observation).where(Observation.field == "kills")).one()
    assert obs.invalid_reason == "impossible"


def test_un_marcador_ilegible_marca_las_dos_observaciones(session, ingest):
    from tests.integration.ingest.test_matches import base, match
    ingest([*base(), match(status="live", maps_won=[1, 0])])
    ingest([match(hours=1, status="live", unreadable=["maps_won"])])
    fields = {o.field: o.invalid_reason for o in session.scalars(select(Observation))
              if o.field.startswith("maps_won")}
    assert fields == {"maps_won_1": "unreadable", "maps_won_2": "unreadable"}
