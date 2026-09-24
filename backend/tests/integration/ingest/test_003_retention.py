"""T-043 · Registros retenidos (spec 003: RF-54, RF-55 con la nota C-14).

Una referencia sin enlazar de una fuente, cuando otra de más prioridad publica ese tipo, queda
retenida: no aparece en los datos de la temporada actual (listas de jugadores, equipos, eventos
y partidos), pero el historial de campeonatos sí la usa (C-14). Se informa en la ingesta.
"""

from datetime import UTC, datetime

from sqlalchemy import select

from app.api import views
from app.db.models import ExternalRef
from tests.integration.ingest.helpers import rec, team
from tests.integration.ingest.test_matches import base, match

NOW = datetime(2026, 1, 11, 12, 0, tzinfo=UTC)


def ref(session, key):
    source, source_id = key.split(":", 1)
    session.expire_all()
    return session.scalars(select(ExternalRef).where(ExternalRef.source == source, ExternalRef.source_id == source_id)).one()


def gamertags(session):
    return [p.current_gamertag for p in views.player_views(session, NOW)]


def test_un_jugador_de_la_wiki_sin_enlazar_queda_retenido_y_no_se_lista(session, ingest):
    report = ingest([rec("player", "p1", gamertag="[FICTICIO] Uno"),
                     rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno (Wiki)")], now=NOW)
    assert ref(session, "wiki:Uno").retained_since == NOW
    assert ref(session, "bp:p1").retained_since is None
    assert report.retained == ["wiki:Uno"]
    assert gamertags(session) == ["[FICTICIO] Uno"]


def test_un_jugador_enlazado_no_queda_retenido(session, ingest):
    ingest([rec("player", "p1", gamertag="[FICTICIO] Uno"),
            rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno", same_as=["bp:p1"])], now=NOW)
    assert ref(session, "wiki:Uno").retained_since is None


def test_se_retiene_cuando_la_fuente_principal_empieza_a_publicar_ese_tipo(session, ingest):
    ingest([rec("player", "Uno", source="wiki", gamertag="[FICTICIO] Uno (Wiki)")], now=NOW)
    assert ref(session, "wiki:Uno").retained_since is None
    report = ingest([rec("player", "p1", hours=1, gamertag="[FICTICIO] Uno")], now=NOW)
    assert ref(session, "wiki:Uno").retained_since == NOW
    assert report.retained == ["wiki:Uno"]


def test_la_fecha_de_retencion_no_se_mueve_ni_se_vuelve_a_informar(session, ingest):
    records = [rec("player", "p1", gamertag="[FICTICIO] Uno"), rec("player", "Uno", source="wiki", gamertag="[FICTICIO] W")]
    ingest(records, now=NOW)
    report = ingest(records, now=NOW.replace(hour=13))
    assert ref(session, "wiki:Uno").retained_since == NOW
    assert report.retained == []


def test_un_partido_de_la_wiki_sin_enlace_no_duplica_el_de_breakingpoint(session, ingest):
    # Un partido en vivo hace que la temporada empiece y haya "temporada actual" (RF-2 de la 002).
    report = ingest([*base(), match(status="live"),
                     rec("match", "M1", source="wiki", event_ref="bp:ev1", best_of=5, status="live")], now=NOW)
    assert report.retained == ["wiki:M1"]
    assert len(views.match_views(session, NOW)) == 1


def test_equipos_y_eventos_retenidos_no_se_listan(session, ingest):
    ingest([*base(), match(status="live"), *team("Otro", "[FICTICIO] Otro (Wiki)", source="wiki"),
            rec("event", "Ev", source="wiki", season_year=2026, name="[FICTICIO] Evento Wiki")], now=NOW)
    names = [f.identities[-1].short_name for f in views.franchise_views(session)]
    assert names == ["[FICTICIO] Dos", "[FICTICIO] Uno"]
    assert [e.name for e in views.event_views(session)] == ["[FICTICIO] Major 2026"]


def test_el_historial_usa_los_registros_retenidos(session, ingest):
    # C-14: BreakingPoint no publica historial, así que la Wiki no puede duplicarlo.
    ingest([*base(), rec("player", "p1", gamertag="[FICTICIO] Uno"),
            *team("Viejo", "[FICTICIO] Equipo de 2019", source="wiki"),
            rec("player", "Veterano", source="wiki", gamertag="[FICTICIO] Veterano"),
            rec("championship", "C2019", source="wiki", year=2019, competition="CWL Championship",
                game_name="Call of Duty: Black Ops 4", game_abbreviation="BO4", final_date="2019-08-18", completed=True),
            rec("placement", "P", source="wiki", championship_ref="wiki:C2019", franchise_ref="wiki:Viejo",
                published_team_name="[FICTICIO] Equipo de 2019", place="1",
                roster=[{"player_ref": "wiki:Veterano", "gamertag_at_final": "[FICTICIO] Veterano"}])], now=NOW)
    assert ref(session, "wiki:Viejo").retained_since == NOW
    (championship,) = views.championship_views(session)
    (placement,) = championship.placements
    assert placement.identity.short_name == "[FICTICIO] Equipo de 2019"
    assert [entry.current_gamertag for entry in placement.roster] == ["[FICTICIO] Veterano"]
