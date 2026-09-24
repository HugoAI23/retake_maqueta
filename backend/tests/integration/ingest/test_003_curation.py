"""T-044 · Curación: `merges` (partidos, eventos y franquicias) y `confirmed_new` (spec 003: RF-54, RF-56).

Unir o confirmar libera un registro retenido. Un error de formato no aplica nada (como en la 002).
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.curation.loader import Curation, CurationError, parse_curation
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


# --- Plan I-37: unir franquicias no deja identidades repetidas ------------------------------------

OPTIC = parse_curation("merges: [ {kind: franchise, refs: ['bp:4', 'wiki:OpTic_TEX'], reason: 'x'} ]")


def wiki_champs(hours):
    return [
        rec("championship", "Champs_2023", source="wiki", hours=hours, year=2023, competition="champs",
            game_name="[FICTICIO] Juego", game_abbreviation="FJ", final_date="2023-06-18", completed=True),
        *team("OpTic_TEX", "[FICTICIO] OpTic TEX", source="wiki", hours=hours),
        rec("placement", "Champs_2023/OpTic_TEX", source="wiki", hours=hours, championship_ref="wiki:Champs_2023",
            franchise_ref="wiki:OpTic_TEX", published_team_name="[FICTICIO] OpTic TEX", place="1"),
    ]


def identities(session):
    session.expire_all()
    return session.scalars(select(Identity).order_by(Identity.valid_from)).all()


def test_unir_franquicias_ya_cargadas_no_deja_identidades_repetidas(session, ingest):
    # Lo que pasó en la primera carga real: la franquicia de la Wiki ya existía, con su clasificación,
    # cuando la curación la unió a la de BreakingPoint.
    from tests.integration.ingest.helpers import season_and_event

    ingest([*season_and_event(), *team("4", "[FICTICIO] OpTic Texas", abbreviation="TX")])
    first_start = identities(session)[0].valid_from
    ingest(wiki_champs(5))
    ingest(wiki_champs(6), curation=OPTIC)
    (identity,) = identities(session)
    assert identity.short_name == "[FICTICIO] OpTic Texas"
    assert identity.valid_from == first_start  # conserva la fecha de la identidad más antigua
    refs = set(session.scalars(select(ExternalRef.source_id).where(
        ExternalRef.kind == "identity", ExternalRef.entity_id == identity.id)))
    assert refs == {"4-id", "OpTic_TEX-id"}
    from app.db.models import Placement
    assert session.scalars(select(Placement.identity_id)).all() == [identity.id]


def test_aplicar_la_curacion_junta_identidades_repetidas_ya_guardadas(session, ingest):
    # Arregla las bases donde ya pasó: dos identidades seguidas con los mismos datos se juntan en la
    # más antigua; un cambio de nombre de verdad sigue siendo historial (RF-73 de la 002).
    from app.db.models import Placement
    from tests.integration.ingest.helpers import season_and_event

    ingest([*season_and_event(), *team("4", "[FICTICIO] Nombre antiguo", abbreviation="OLD")])
    ingest([*team("4", "[FICTICIO] OpTic Texas", abbreviation="TX", hours=2)])
    ingest(wiki_champs(3))
    old, current = identities(session)[:2]
    franchise_id = current.franchise_id
    repeated = Identity(franchise_id=franchise_id, valid_from=current.valid_from + timedelta(hours=5),
                        short_name=current.short_name, abbreviation=current.abbreviation)
    session.add(repeated)
    session.flush()
    session.execute(ExternalRef.__table__.update().where(ExternalRef.entity_id == current.id).values(entity_id=repeated.id))
    session.commit()
    before = {i.short_name for i in identities(session) if i.franchise_id == franchise_id}
    assert len([i for i in identities(session) if i.franchise_id == franchise_id]) == 3

    apply_curation(session, Curation())
    session.commit()
    rows = [i for i in identities(session) if i.franchise_id == franchise_id]
    assert [(i.short_name, i.valid_from) for i in rows] == [(old.short_name, old.valid_from),
                                                          (current.short_name, current.valid_from)]
    assert {i.short_name for i in rows} == before
    kept = rows[1].id
    assert set(session.scalars(select(ExternalRef.entity_id).where(
        ExternalRef.kind == "identity", ExternalRef.source == "bp"))) == {kept}
