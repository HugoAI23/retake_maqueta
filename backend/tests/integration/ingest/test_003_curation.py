"""T-044 · Curación: `merges` (partidos, eventos y franquicias) y `confirmed_new` (spec 003: RF-54, RF-56).

Unir o confirmar libera un registro retenido. Un error de formato no aplica nada (como en la 002).
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.curation.loader import CurationError, parse_curation
from app.curation.overlay import apply_curation
from app.db.models import Event, ExternalRef, Franchise, Identity, Match
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec, team
from tests.integration.ingest.test_matches import base, match

NOW = datetime(2026, 1, 11, 12, 0, tzinfo=UTC)


def count(session, model):
    session.expire_all()
    return session.scalar(select(func.count()).select_from(model))


def retained(session, key):
    source, source_id = key.split(":", 1)
    session.expire_all()
    return session.scalars(select(ExternalRef.retained_since).where(
        ExternalRef.source == source, ExternalRef.source_id == source_id)).first()


def wiki_match():
    return rec("match", "M1", source="wiki", event_ref="bp:ev1", best_of=5, status="scheduled")


def test_unir_dos_partidos_libera_el_retenido(session, ingest):
    ingest([*base(), match(status="scheduled"), wiki_match()], now=NOW)
    assert retained(session, "wiki:M1") == NOW
    curation = parse_curation("merges: [ {kind: match, refs: ['bp:m1', 'wiki:M1'], reason: 'mismo partido'} ]")
    ingest([wiki_match()], curation=curation, now=NOW)
    assert count(session, Match) == 1
    assert retained(session, "wiki:M1") is None
    assert entity_for(session, "match", "wiki:M1") == entity_for(session, "match", "bp:m1")


def test_unir_franquicias_junta_sus_identidades(session, ingest):
    ingest([*team("t1", "[FICTICIO] Equipo", abbreviation="FEQ"),
            *team("Team", "[FICTICIO] Equipo", source="wiki", secondary_color="#ffffff")], now=NOW)
    assert count(session, Franchise) == 2
    apply_curation(session, parse_curation("merges: [ {kind: franchise, refs: ['bp:t1', 'wiki:Team'], reason: 'x'} ]"))
    session.commit()
    assert count(session, Franchise) == 1
    (identity,) = session.scalars(select(Identity)).all()
    assert (identity.abbreviation, identity.secondary_color) == ("FEQ", "#ffffff")
    assert retained(session, "wiki:Team") is None


def test_unir_eventos(session, ingest):
    ingest([*base(), rec("event", "Ev", source="wiki", season_year=2026, name="[FICTICIO] Evento Wiki")], now=NOW)
    apply_curation(session, parse_curation("merges: [ {kind: event, refs: ['bp:ev1', 'wiki:Ev'], reason: 'x'} ]"))
    session.commit()
    assert count(session, Event) == 1


def test_confirmar_como_nuevo_libera_el_retenido(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno"), rec("player", "Otro", source="wiki", gamertag="[FICTICIO] Otro")],
           now=NOW)
    assert retained(session, "wiki:Otro") == NOW
    apply_curation(session, parse_curation("confirmed_new: [ {kind: player, ref: 'wiki:Otro', reason: 'jugador nuevo'} ]"))
    session.commit()
    assert retained(session, "wiki:Otro") is None


@pytest.mark.parametrize("text", [
    "merges: [ {kind: player, refs: ['bp:p1', 'wiki:P'], reason: 'x'} ]",      # los jugadores van en player_merges
    "merges: [ {kind: match, refs: ['bp:m1'], reason: 'x'} ]",                  # hacen falta dos referencias
    "merges: [ {kind: match, refs: ['bp:m1', 'wiki:M1']} ]",                    # sin motivo
    "confirmed_new: [ {kind: identity, ref: 'wiki:X', reason: 'x'} ]",          # tipo que no se retiene
    "confirmed_new: [ {kind: player, ref: 'wiki:X'} ]",                         # sin motivo
])
def test_un_error_de_formato_es_un_error(text):
    with pytest.raises(CurationError):
        parse_curation(text)


def test_una_referencia_desconocida_no_aplica_nada(session, ingest):
    ingest([*base(), match(status="scheduled"), wiki_match()], now=NOW)
    with pytest.raises(CurationError, match="wiki:Fantasma"):
        apply_curation(session, parse_curation(
            "merges: [ {kind: match, refs: ['bp:m1', 'wiki:M1'], reason: 'x'} ]\n"
            "confirmed_new: [ {kind: player, ref: 'wiki:Fantasma', reason: 'x'} ]"))
    session.rollback()
    assert count(session, Match) == 2
