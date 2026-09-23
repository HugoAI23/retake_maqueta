"""T-032 y T-041 · Temporadas, eventos, franquicias e identidades; seguridad de la entrada."""

from datetime import UTC, datetime

from sqlalchemy import func, select

from app.db.models import Event, Franchise, Identity, Player, Season
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import T0, rec, team


def test_temporada_por_anio_oficial_y_evento_tal_cual(session, ingest):
    ingest([rec("season", "s", year=2026, name="CDL 2026"),
            rec("event", "e", season_year=2026, name="  [FICTICIO] Major 2 Qualifiers ")])
    season = session.scalars(select(Season)).one()
    assert (season.year, season.name) == (2026, "CDL 2026")
    assert session.scalars(select(Event)).one().name == "  [FICTICIO] Major 2 Qualifiers "


def test_dos_fuentes_con_el_mismo_anio_son_la_misma_temporada(session, ingest):
    ingest([rec("season", "s", year=2026), rec("season", "CDL_2026", source="wiki", year=2026, name="CDL 2026")])
    assert session.scalar(select(func.count()).select_from(Season)) == 1


def test_una_franquicia_con_predecesora_es_la_misma(session, ingest):
    ingest([rec("franchise", "Old_City", source="wiki"),
            rec("franchise", "New_City", source="wiki", predecessor="wiki:Old_City")])
    assert entity_for(session, "franchise", "wiki:Old_City") == entity_for(session, "franchise", "wiki:New_City")
    assert session.scalar(select(func.count()).select_from(Franchise)) == 1


def test_una_franquicia_sin_predecesora_es_nueva(session, ingest):
    ingest([rec("franchise", "Old_City", source="wiki"), rec("franchise", "Fresh", source="wiki")])
    assert session.scalar(select(func.count()).select_from(Franchise)) == 2


def identities(session):
    return session.scalars(select(Identity).order_by(Identity.valid_from)).all()


def test_repetir_la_misma_identidad_no_crea_otra(session, ingest):
    ingest(team("t1", "[FICTICIO] Equipo", abbreviation="FEQ", primary_color="#112233"))
    ingest(team("t1", "[FICTICIO] Equipo", hours=1, abbreviation="FEQ", primary_color="#112233"))
    assert len(identities(session)) == 1


def test_cambiar_solo_el_color_secundario_crea_una_identidad_nueva(session, ingest):
    ingest(team("t1", "[FICTICIO] Equipo", abbreviation="FEQ", secondary_color="#000000"))
    ingest(team("t1", "[FICTICIO] Equipo", hours=3, abbreviation="FEQ", secondary_color="#ffffff"))
    old, new = identities(session)
    assert (old.secondary_color, new.secondary_color) == ("#000000", "#ffffff")
    assert old.valid_from == T0
    assert new.valid_from == datetime(2026, 1, 10, 15, 0, tzinfo=UTC)  # instante de observación


def test_la_fecha_de_vigencia_publicada_manda(session, ingest):
    ingest(team("t1", "[FICTICIO] Equipo", valid_from="2020-01-01T00:00:00Z"))
    assert identities(session)[0].valid_from == datetime(2020, 1, 1, tzinfo=UTC)


def test_la_misma_identidad_publicada_por_otra_fuente_no_se_duplica(session, ingest):
    ingest([*team("t1", "[FICTICIO] Equipo", abbreviation="FEQ"),
            rec("franchise", "Team", source="wiki", same_as=["bp:t1"]),
            rec("identity", "Team-id", source="wiki", hours=2, franchise_ref="wiki:Team",
                short_name="[FICTICIO] Equipo", abbreviation="FEQ")])
    assert len(identities(session)) == 1


def test_un_logo_no_valido_queda_ausente_sin_perder_el_resto(session, ingest):
    ingest(team("t1", "[FICTICIO] Equipo", abbreviation="FEQ", logo_url="javascript:alert(1)"))
    identity = identities(session)[0]
    assert identity.logo_url is None
    assert identity.abbreviation == "FEQ"


def test_un_gamertag_con_html_llega_sin_cambios(session, ingest):
    gamertag = '[FICTICIO] <img src=x onerror="alert(1)">'
    ingest([rec("player", "p1", gamertag=gamertag)])
    assert session.scalars(select(Player)).one().current_gamertag == gamertag


def test_los_equipos_del_historial_son_franquicias_con_identidad(session, ingest):
    ingest(team("OpTic_2017", "[FICTICIO] Equipo 2017", source="wiki", valid_from="2017-01-01T00:00:00Z"))
    assert session.scalar(select(func.count()).select_from(Franchise)) == 1
    assert identities(session)[0].short_name == "[FICTICIO] Equipo 2017"
