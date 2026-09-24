"""T-093 · Tabla de países de la curación (registro I-6 del plan; RF-22 de la 002, RF-48 y RF-142 de la 003).

BreakingPoint solo publica un número de país (`bp:<n>`). La sección `countries` lo traduce. Un
número sin traducir es un dato no entendido: cede el turno a otra fuente (RF-48) y, si ninguna lo
publica, el país queda `No disponible` y se anota la incidencia.
"""

import pytest

from app.curation.loader import CurationError, parse_curation
from app.db.models import Player
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec

COUNTRIES = parse_curation('countries: {12: "México", 40: "Estados Unidos"}')


def country(session, key="bp:p1"):
    session.expire_all()
    return session.get(Player, entity_for(session, "player", key)).country


def test_el_numero_de_breakingpoint_se_traduce(session, ingest):
    report = ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", country="bp:12")], curation=COUNTRIES)
    assert country(session) == "México"
    assert report.untranslated_countries == []


def test_un_numero_sin_traducir_queda_sin_pais_y_se_anota(session, ingest):
    report = ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", country="bp:99")], curation=COUNTRIES)
    assert country(session) is None
    (incident,) = report.untranslated_countries
    assert (incident.ref, incident.reason) == ("bp:p1", "país de BreakingPoint sin traducir: 99")


def test_sin_traduccion_manda_el_pais_de_otra_fuente(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", country="bp:99"),
            rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno", same_as=["bp:p1"], country="Canadá")],
           curation=COUNTRIES)
    assert country(session) == "Canadá"


def test_con_traduccion_manda_breakingpoint(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno", country="bp:12"),
            rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno", same_as=["bp:p1"], country="Canadá")],
           curation=COUNTRIES)
    assert country(session) == "México"


def test_el_pais_de_la_wiki_llega_tal_cual(session, ingest):
    ingest([rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno", country="Canadá")], curation=COUNTRIES)
    assert country(session, "wiki:Uno") == "Canadá"


@pytest.mark.parametrize("text", [
    'countries: {0: "México"}',       # número no válido
    'countries: {12: ""}',            # nombre vacío
    'countries: {"doce": "México"}',  # no es un número
])
def test_una_tabla_de_paises_mal_escrita_es_un_error(text):
    with pytest.raises(CurationError):
        parse_curation(text)
