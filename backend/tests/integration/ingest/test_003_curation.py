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


# --- Plan I-45: unir franquicias de la Wiki conserva sus nombres antiguos -------------------------


def wiki_history(folder):
    """Historial de la Wiki con una franquicia que cambia de nombre: Dallas (2020-2021) y Texas (2022-)."""
    from app.sources import wiki_csv
    from app.sources.wiki_csv import read_wiki_csv
    from tests.unit.sources.test_wiki_csv import BIRTHDAY_COLUMNS, HISTORY_COLUMNS, history_row, write

    write(folder / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2020", "[FICTICIO] Dallas", "[FICTICIO] Uno", final="2020-08-30"),
        history_row("3", "2021", "[FICTICIO] Dallas", "[FICTICIO] Uno", final="2021-08-22"),
        history_row("4", "2022", "[FICTICIO] Texas", "[FICTICIO] Uno", final="2022-08-07"),
        history_row("2", "2026", "[FICTICIO] Texas", "[FICTICIO] Uno", final="2026-07-19"),
    ])
    write(folder / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [])
    return read_wiki_csv(folder, NOW.replace(month=9))


def names_by_year(session):
    from app.db.models import Championship, Placement

    session.expire_all()
    return dict(session.execute(
        select(Championship.year, Identity.short_name)
        .join(Placement, Placement.championship_id == Championship.id)
        .join(Identity, Identity.id == Placement.identity_id).order_by(Championship.year)).all())


WIKI_RENAME = parse_curation(
    "merges: [ {kind: franchise, refs: ['wiki:[FICTICIO]_Dallas', 'wiki:[FICTICIO]_Texas'], reason: 'x'} ]")


def test_unir_dos_franquicias_de_la_wiki_conserva_los_dos_nombres(session, ingest, tmp_path):
    ingest(wiki_history(tmp_path).records)
    apply_curation(session, WIKI_RENAME)
    session.commit()
    assert [i.short_name for i in identities(session)] == ["[FICTICIO] Dallas", "[FICTICIO] Texas"]
    # Cada puesto con la identidad vigente en su final (RF-13 de la 002).
    assert names_by_year(session) == {2020: "[FICTICIO] Dallas", 2021: "[FICTICIO] Dallas",
                                      2022: "[FICTICIO] Texas", 2026: "[FICTICIO] Texas"}


def test_una_franquicia_actual_unida_a_su_nombre_antiguo_sigue_con_el_actual_en_la_temporada(session, ingest, tmp_path):
    from app.domain.identities import identity_at
    from app.ingest.resolvers import franchise_identities
    from tests.integration.ingest.helpers import T0, season_and_event

    ingest([*season_and_event(), *team("4", "[FICTICIO] OpTic Texas", abbreviation="TX")])
    ingest(wiki_history(tmp_path).records)
    apply_curation(session, parse_curation(
        "merges: [ {kind: franchise, refs: ['bp:4', 'wiki:[FICTICIO]_Texas', 'wiki:[FICTICIO]_Dallas'], reason: 'x'} ]"))
    session.commit()
    assert [i.short_name for i in identities(session)] == ["[FICTICIO] Dallas", "[FICTICIO] OpTic Texas"]
    assert names_by_year(session) == {2020: "[FICTICIO] Dallas", 2021: "[FICTICIO] Dallas",
                                      2022: "[FICTICIO] OpTic Texas", 2026: "[FICTICIO] OpTic Texas"}
    # Un partido de la temporada 2026 (RF-12 de la 002) lleva el nombre actual.
    franchise_id = entity_for(session, "franchise", "bp:4")
    assert identity_at(franchise_identities(session, franchise_id), T0).data.short_name == "[FICTICIO] OpTic Texas"


def test_reimportar_la_wiki_fecha_las_identidades_ya_guardadas_sin_fecha(session, ingest, tmp_path):
    # Las bases cargadas antes de I-45 tienen las identidades de la Wiki con la hora de la importación.
    records = wiki_history(tmp_path).records
    ingest([{k: v for k, v in r.items() if k != "valid_from"} for r in records])
    ingest(records)
    apply_curation(session, WIKI_RENAME)
    session.commit()
    assert [(i.short_name, i.valid_from) for i in identities(session)] == [
        ("[FICTICIO] Dallas", datetime(2020, 1, 1, tzinfo=UTC)),
        ("[FICTICIO] Texas", datetime(2021, 8, 23, tzinfo=UTC)),
    ]
    assert names_by_year(session)[2021] == "[FICTICIO] Dallas"


def test_una_franquicia_sin_champs_toma_su_nombre_del_roster_y_conserva_el_anterior(session, ingest, tmp_path):
    # Cambio C-28: Cloud9 New York aún no ha jugado un Champs; sin el nombre de su roster en la Wiki,
    # NY Subliners se tomaba por su nombre vigente y el historial salía con el nombre nuevo.
    from app.sources import wiki_csv
    from app.sources.wiki_csv import read_wiki_csv
    from tests.integration.ingest.helpers import season_and_event
    from tests.unit.sources.test_wiki_csv import BIRTHDAY_COLUMNS, HISTORY_COLUMNS, ROSTER_COLUMNS, history_row, write

    write(tmp_path / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2023", "[FICTICIO] Subliners", "[FICTICIO] Uno", final="2023-06-18"),
        history_row("2", "2024", "[FICTICIO] Subliners", "[FICTICIO] Uno", final="2024-07-21"),
        history_row("1", "2025", "[FICTICIO] Otro", "[FICTICIO] Dos", final="2025-06-29"),
    ])
    write(tmp_path / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [])
    write(tmp_path / "cdl_2026_rosters.csv", ROSTER_COLUMNS,
          [["[FICTICIO] Cloud9 NY", "", "[FICTICIO] Uno", "", "", "", "", "", "", "", ""]])
    ingest([*season_and_event(), *team("63", "[FICTICIO] Cloud9 New York", abbreviation="C9NY")])
    ingest(read_wiki_csv(tmp_path, NOW.replace(month=9)).records)
    apply_curation(session, parse_curation(
        "merges: [ {kind: franchise, refs: ['bp:63', 'wiki:[FICTICIO]_Cloud9_NY', 'wiki:[FICTICIO]_Subliners'],"
        " reason: 'x'} ]"))
    session.commit()
    franchise_id = entity_for(session, "franchise", "bp:63")
    rows = [i for i in identities(session) if i.franchise_id == franchise_id]
    assert [i.short_name for i in rows] == ["[FICTICIO] Subliners", "[FICTICIO] Cloud9 New York"]
    assert {y: n for y, n in names_by_year(session).items() if y < 2025} == {
        2023: "[FICTICIO] Subliners", 2024: "[FICTICIO] Subliners"}


# La importación aplica la curación: las uniones ya están activas cuando llegan los nombres de la Wiki
# (instalación nueva, o cada importación tras un Champs). El resultado no debe depender del orden.

def cloud9_history(folder):
    from app.sources import wiki_csv
    from app.sources.wiki_csv import read_wiki_csv
    from tests.unit.sources.test_wiki_csv import BIRTHDAY_COLUMNS, HISTORY_COLUMNS, ROSTER_COLUMNS, history_row, write

    write(folder / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2023", "[FICTICIO] Subliners", "[FICTICIO] Uno", final="2023-06-18"),
        history_row("2", "2024", "[FICTICIO] Subliners", "[FICTICIO] Uno", final="2024-07-21"),
        history_row("1", "2025", "[FICTICIO] Otro", "[FICTICIO] Dos", final="2025-06-29"),
    ])
    write(folder / wiki_csv.BIRTHDAYS_FILE, BIRTHDAY_COLUMNS, [])
    write(folder / "cdl_2026_rosters.csv", ROSTER_COLUMNS,
          [["[FICTICIO] Cloud9 NY", "", "[FICTICIO] Uno", "", "", "", "", "", "", "", ""]])
    return read_wiki_csv(folder, NOW.replace(month=9)).records


CLOUD9 = parse_curation(
    "merges: [ {kind: franchise, refs: ['bp:63', 'wiki:[FICTICIO]_Cloud9_NY', 'wiki:[FICTICIO]_Subliners'], reason: 'x'} ]")


def cloud9_names(session):
    franchise_id = entity_for(session, "franchise", "bp:63")
    return [i.short_name for i in identities(session) if i.franchise_id == franchise_id]


def test_importar_con_la_union_ya_en_la_curacion_conserva_el_nombre_anterior(session, ingest, tmp_path):
    from tests.integration.ingest.helpers import season_and_event

    ingest([*season_and_event(), *team("63", "[FICTICIO] Cloud9 New York", abbreviation="C9NY")], curation=CLOUD9)
    ingest(cloud9_history(tmp_path), curation=CLOUD9)
    assert cloud9_names(session) == ["[FICTICIO] Subliners", "[FICTICIO] Cloud9 New York"]
    assert {y: n for y, n in names_by_year(session).items() if y < 2025} == {
        2023: "[FICTICIO] Subliners", 2024: "[FICTICIO] Subliners"}


def test_importar_dos_franquicias_de_la_wiki_ya_unidas_conserva_los_dos_nombres(session, ingest, tmp_path):
    ingest(wiki_history(tmp_path).records, curation=WIKI_RENAME)
    assert [i.short_name for i in identities(session)] == ["[FICTICIO] Dallas", "[FICTICIO] Texas"]
    assert names_by_year(session)[2021] == "[FICTICIO] Dallas"


def test_reimportar_con_las_uniones_ya_aplicadas_no_cambia_nada(session, ingest, tmp_path):
    from tests.integration.ingest.helpers import season_and_event

    ingest([*season_and_event(), *team("63", "[FICTICIO] Cloud9 New York", abbreviation="C9NY")])
    records = cloud9_history(tmp_path)
    ingest(records)
    apply_curation(session, CLOUD9)
    session.commit()
    before = [(i.short_name, i.valid_from) for i in identities(session)]
    ingest(records, curation=CLOUD9)
    assert [(i.short_name, i.valid_from) for i in identities(session)] == before


def test_reimportar_con_las_uniones_ya_en_la_curacion_fecha_los_nombres_sin_fecha(session, ingest, tmp_path):
    # Bases cargadas antes de I-45: los nombres de la Wiki, con la hora de la importación y aún sin unir.
    records = wiki_history(tmp_path).records
    ingest([{k: v for k, v in r.items() if k != "valid_from"} for r in records])
    ingest(records, curation=WIKI_RENAME)
    assert [(i.short_name, i.valid_from) for i in identities(session)] == [
        ("[FICTICIO] Dallas", datetime(2020, 1, 1, tzinfo=UTC)),
        ("[FICTICIO] Texas", datetime(2021, 8, 23, tzinfo=UTC)),
    ]
    assert names_by_year(session)[2021] == "[FICTICIO] Dallas"


def test_nombres_sin_fecha_importados_a_distinta_hora_toman_su_fecha_al_reimportar_ya_unidos(session, ingest, tmp_path):
    # Como Chicago en la base real: el nombre nuevo se guardó en una importación posterior.
    from datetime import timedelta

    records = wiki_history(tmp_path).records
    undated = [{k: v for k, v in r.items() if k != "valid_from"} for r in records]
    later = (NOW.replace(month=9) + timedelta(minutes=16)).isoformat()
    ingest([r for r in undated if "Texas" not in r["source_id"]])
    ingest([{**r, "observed_at": later} for r in undated if "Texas" in r["source_id"]])
    ingest(records, curation=WIKI_RENAME)
    assert [(i.short_name, i.valid_from) for i in identities(session)] == [
        ("[FICTICIO] Dallas", datetime(2020, 1, 1, tzinfo=UTC)),
        ("[FICTICIO] Texas", datetime(2021, 8, 23, tzinfo=UTC)),
    ]
    assert names_by_year(session)[2021] == "[FICTICIO] Dallas"
