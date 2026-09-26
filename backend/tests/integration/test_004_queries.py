"""T-006 de la spec 004 · Consultas del balance y de la identidad de cada fila (RF-41a; RF-136 de la 002)."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Season
from app.db.queries import finished_season_matches, last_played_at, season_has_matches
from app.domain.season_balance import FinishedMatch
from app.ingest.store import entity_for
from tests.integration.api.test_003_api import ingest, rec


def base():
    return [
        rec("season", "s25", year=2025, name="CDL 2025"),
        rec("season", "s26", year=2026, name="CDL 2026"),
        rec("event", "e25", season_year=2025, name="[FICTICIO] Major 2025"),
        rec("event", "e26", season_year=2026, name="[FICTICIO] Major 2026"),
        rec("franchise", "t1"), rec("identity", "t1-id", franchise_ref="bp:t1", short_name="[FICTICIO] Uno"),
        rec("franchise", "t2"), rec("identity", "t2-id", franchise_ref="bp:t2", short_name="[FICTICIO] Dos"),
        rec("franchise", "t3"), rec("identity", "t3-id", franchise_ref="bp:t3", short_name="[FICTICIO] Tres"),
    ]


def match(sid, status, when, event="bp:e26", sides=("bp:t1", "bp:t2"), **fields):
    return rec("match", sid, event_ref=event, best_of=5, status=status, scheduled_at=when,
               slots=[{"franchise_ref": side} for side in sides], **fields)


def season_id(session, year):
    return session.scalar(select(Season.id).where(Season.year == year))


def test_solo_los_partidos_finalizados_de_la_temporada_con_sus_lados_ganador_y_marcador(clean_db):
    ingest(clean_db, [
        *base(),
        match("m1", "finished", "2026-01-10T11:00:00Z", maps_won=[3, 1], winner_side=1),
        match("m2", "finished", "2026-01-11T11:00:00Z", sides=("bp:t2", "bp:t3"), winner_side=2),
        match("m3", "live", "2026-01-12T11:00:00Z", maps_won=[1, 0]),
        match("m4", "scheduled", "2026-01-13T11:00:00Z"),
        match("m5", "finished", "2025-01-10T11:00:00Z", event="bp:e25", maps_won=[3, 0], winner_side=1),
    ])
    with Session(clean_db) as session:
        t1, t2, t3 = (entity_for(session, "franchise", f"bp:{t}") for t in ("t1", "t2", "t3"))
        rows = finished_season_matches(session, season_id(session, 2026))
        assert sorted((row.result for row in rows), key=lambda r: r.winner_side) == [
            FinishedMatch(sides=(t1, t2), winner_side=1, maps_won=(3, 1)),
            FinishedMatch(sides=(t2, t3), winner_side=2, maps_won=(None, None)),
        ]
        assert all(row.changed_at is not None for row in rows)


def test_ultimo_partido_jugado_de_cada_franquicia_por_su_hora_programada(clean_db):
    ingest(clean_db, [
        *base(),
        # Se registran en otro orden que el de su hora programada.
        match("m2", "live", "2026-02-01T11:00:00Z", maps_won=[1, 0]),
        match("m1", "finished", "2026-01-10T11:00:00Z", maps_won=[3, 1], winner_side=1),
        match("m3", "scheduled", "2026-03-01T11:00:00Z", sides=("bp:t1", "bp:t3")),
        match("m4", "finished", "2025-06-01T11:00:00Z", event="bp:e25", sides=("bp:t3", "bp:t2"),
              maps_won=[3, 0], winner_side=1),
    ])
    with Session(clean_db) as session:
        t1, t2 = (entity_for(session, "franchise", f"bp:{t}") for t in ("t1", "t2"))
        # t3 solo tiene un partido programado de 2026 y uno jugado de 2025: no cuenta.
        assert last_played_at(session, season_id(session, 2026)) == {
            t1: datetime(2026, 2, 1, 11, 0, tzinfo=UTC),
            t2: datetime(2026, 2, 1, 11, 0, tzinfo=UTC),
        }


def test_un_partido_reprogramado_cuenta_por_su_ultima_hora(clean_db):
    ingest(clean_db, [*base(), match("m1", "finished", "2026-01-10T11:00:00Z", maps_won=[3, 1], winner_side=1)])
    ingest(clean_db, [match("m1", "finished", "2026-01-12T15:00:00Z", maps_won=[3, 1], winner_side=1)])
    with Session(clean_db) as session:
        t1 = entity_for(session, "franchise", "bp:t1")
        assert last_played_at(session, season_id(session, 2026))[t1] == datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def test_la_temporada_tiene_partidos_si_hay_alguno_en_cualquier_estado(clean_db):
    ingest(clean_db, [*base(), match("m5", "finished", "2025-01-10T11:00:00Z", event="bp:e25",
                                     maps_won=[3, 0], winner_side=1)])
    with Session(clean_db) as session:
        assert season_has_matches(session, season_id(session, 2026)) is False
    ingest(clean_db, [match("m4", "scheduled", "2026-01-13T11:00:00Z")])
    with Session(clean_db) as session:
        assert season_has_matches(session, season_id(session, 2026)) is True
