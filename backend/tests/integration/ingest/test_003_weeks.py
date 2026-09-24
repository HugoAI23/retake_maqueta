"""T-092 · Semana de los partidos de clasificatorio (C-13; RF-31 de la 002 revisado).

Si la fuente no publica la semana, es el orden de la semana (lunes a domingo, hora de Ciudad
de México) entre las semanas con partidos del evento. Anclas de la muestra real de la Wiki:
2025-12-05 es "Week 1" y 2026-01-18 es "Week 4"; las semanas 2 y 3 son fechas de prueba.
"""

from sqlalchemy import select

from app.db.models import Match
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec, season_and_event

DATES = {"q1": "2025-12-05T21:30:00Z", "q2": "2025-12-13T19:00:00Z", "q3": "2026-01-10T19:00:00Z",
         "q4": "2026-01-18T20:00:00Z"}


def qualifier(source_id, hours=0, **fields):
    fields.setdefault("scheduled_at", DATES.get(source_id))
    return rec("match", source_id, hours=hours, event_ref="bp:ev1", best_of=5, phase="week", status="finished", **fields)


def weeks(session):
    session.expire_all()
    return {sid: session.get(Match, entity_for(session, "match", f"bp:{sid}")).week for sid in ("q1", "q2", "q3", "q4")}


def test_la_semana_de_cada_partido_del_clasificatorio_se_calcula(session, ingest):
    ingest([*season_and_event(), *(qualifier(sid) for sid in DATES)])
    assert weeks(session) == {"q1": 1, "q2": 2, "q3": 3, "q4": 4}


def test_la_semana_se_recalcula_si_llega_un_partido_de_una_semana_anterior(session, ingest):
    ingest([*season_and_event(), qualifier("q2"), qualifier("q3"), qualifier("q4")])
    ingest([qualifier("q1", hours=1)])
    assert weeks(session) == {"q1": 1, "q2": 2, "q3": 3, "q4": 4}


def test_una_semana_publicada_manda_sobre_la_calculada(session, ingest):
    ingest([*season_and_event(), qualifier("q1"), qualifier("q2"), qualifier("q3"), qualifier("q4", week=5)])
    assert weeks(session) == {"q1": 1, "q2": 2, "q3": 3, "q4": 5}


def test_un_partido_que_no_es_de_semana_no_tiene_numero(session, ingest):
    ingest([*season_and_event(), qualifier("q1"),
            rec("match", "f1", event_ref="bp:ev1", best_of=5, phase="grand_final", scheduled_at="2025-12-06T20:00:00Z")])
    session.expire_all()
    final = session.scalars(select(Match).where(Match.phase == "grand_final")).one()
    assert final.week is None
