"""C-22 a C-24 · Equipos que la fuente no lista (spec 003: RF-18a, RF-18b; spec 002: RF-117a a RF-117d).

La franquicia sin listar entra con sus partidos, y la curación la une a su nombre siguiente: los
partidos de la temporada llevan el nombre antiguo y la identidad vigente es la nueva, sin identidades
duplicadas. El equipo que no está en la tabla entra como invitado, con sus partidos.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select

from app.curation.loader import parse_curation
from app.db.models import ExternalRef, Franchise, Identity
from app.domain.identities import identity_at
from app.ingest.resolvers import franchise_identities
from app.ingest.store import entity_for
from app.sources import bp
from tests.integration.ingest.helpers import rec, season_and_event, team
from tests.unit.sources.test_simulated import recording_client

MERGE = parse_curation("merges: [ {kind: franchise, refs: ['bp:1176', 'bp:6'], reason: 'mismo equipo renombrado'} ]")


def is_guest(session, key):
    session.expire_all()
    return session.get(Franchise, entity_for(session, "franchise", key)).is_guest


def refs(session, kind):
    session.expire_all()
    return set(session.scalars(select(ExternalRef.source_id).where(ExternalRef.kind == kind, ExternalRef.source == "bp")))


def test_la_franquicia_sin_listar_entra_con_sus_partidos(session, ingest):
    client, _, clock = recording_client("franquicia_sin_listar")
    result = bp.consult_regular(client, clock.now())
    ingest(result.records, now=clock.now())
    assert {"6", "744"} <= refs(session, "franchise")
    assert {"911", "912", "913"} <= refs(session, "match")
    assert is_guest(session, "bp:6") is False
    assert is_guest(session, "bp:744") is True  # RF-117a de la 002
    assert is_guest(session, "bp:4") is False


def renamed_records(hours=0):
    return [
        *season_and_event(),
        *team("1176", "[FICTICIO] M80 Boston", hours=hours, abbreviation="M80"),
        rec("franchise", "6", hours=hours),
        rec("identity", "6#identity", hours=hours, franchise_ref="bp:6", short_name="[FICTICIO] Boston Breach",
            abbreviation="BOS", valid_from="2021-12-15T00:00:00+00:00"),
    ]


def test_unida_a_su_nombre_siguiente_conserva_el_nombre_antiguo_en_la_temporada(session, ingest):
    ingest(renamed_records(), curation=MERGE)
    assert session.scalar(select(func.count()).select_from(Franchise)) == 1
    franchise_id = entity_for(session, "franchise", "bp:6")
    assert franchise_id == entity_for(session, "franchise", "bp:1176")
    versions = franchise_identities(session, franchise_id)
    in_season = identity_at(versions, datetime(2025, 12, 20, 20, 0, tzinfo=UTC))
    current = identity_at(versions, datetime(2026, 9, 24, tzinfo=UTC))
    assert in_season.data.short_name == "[FICTICIO] Boston Breach"
    assert current.data.short_name == "[FICTICIO] M80 Boston"


def test_volver_a_consultar_no_crea_identidades_nuevas(session, ingest):
    # Las dos referencias son de la misma fuente: no deben turnarse como identidad vigente (I-36).
    ingest(renamed_records(), curation=MERGE)
    first = session.scalar(select(func.count()).select_from(Identity))
    for hours in (1, 2, 3):
        ingest(renamed_records(hours=hours), curation=MERGE)
    assert session.scalar(select(func.count()).select_from(Identity)) == first == 2


def test_un_invitado_que_entra_en_la_lista_deja_de_serlo_y_conserva_sus_identidades(session, ingest):
    # RF-117d de la 002.
    ingest([*season_and_event(), rec("franchise", "744", guest=True),
            rec("identity", "744#identity", franchise_ref="bp:744", short_name="[FICTICIO] Huntsmen")])
    assert is_guest(session, "bp:744") is True
    ingest([rec("franchise", "744", hours=1, guest=False),
            rec("identity", "744#identity", hours=1, franchise_ref="bp:744", short_name="[FICTICIO] Huntsmen")])
    assert is_guest(session, "bp:744") is False
    assert session.scalar(select(func.count()).select_from(Identity)) == 1


def test_un_invitado_unido_a_su_historial_de_la_wiki_sigue_siendo_invitado(session, ingest):
    # La Wiki no publica si un equipo es invitado: manda lo que dice BreakingPoint.
    curation = parse_curation("merges: [ {kind: franchise, refs: ['bp:744', 'wiki:Huntsmen'], reason: 'x'} ]")
    ingest([*season_and_event(), rec("franchise", "744", guest=True), *team("Huntsmen", "[FICTICIO] Huntsmen", source="wiki")],
           curation=curation)
    assert is_guest(session, "bp:744") is True


# --- C-26 · Rosters de equipos que no son de la CDL ni invitados (RF-18c) ---------------------------


def test_un_roster_con_un_equipo_ajeno_a_la_cdl_se_descarta_sin_anotarlo(session, ingest):
    report = ingest([*season_and_event(), *team("4", "[FICTICIO] OpTic Texas"), rec("player", "p1", gamertag="[FICTICIO] Uno"),
                     rec("roster", "2026/4/p1", season_year=2026, franchise_ref="bp:4", player_ref="bp:p1"),
                     rec("roster", "2026/858/p1", season_year=2026, franchise_ref="bp:858", player_ref="bp:p1")])
    assert report.rejected == []
    assert report.discarded == 1
    from app.db.models import RosterMembership
    assert session.scalar(select(func.count()).select_from(RosterMembership)) == 1


def test_otras_referencias_desconocidas_se_siguen_rechazando(session, ingest):
    # Solo se descarta el roster de un equipo ajeno: un partido o un jugador que falta sigue siendo un error (RF-142).
    report = ingest([*season_and_event(), *team("4", "[FICTICIO] OpTic Texas"),
                     rec("roster", "2026/4/p9", season_year=2026, franchise_ref="bp:4", player_ref="bp:p9"),
                     rec("match", "m1", event_ref="bp:ev1", best_of=5, status="scheduled",
                         slots=[{"franchise_ref": "bp:4"}, {"franchise_ref": "bp:858"}])])
    assert len(report.rejected) == 2 and report.discarded == 0
