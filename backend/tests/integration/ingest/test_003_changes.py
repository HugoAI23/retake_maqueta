"""T-038 · Hora del último cambio por fila y por conjunto de datos (spec 003: RF-157 a RF-159)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.models import DatasetChange, Match, Player, Season
from tests.integration.ingest.test_matches import base, match

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)


def dataset_times(session):
    session.expire_all()
    return {row.dataset: row.last_changed_at for row in session.scalars(select(DatasetChange))}


def test_el_primer_registro_de_un_dato_cuenta_como_cambio(session, ingest):
    report = ingest([*base(), match(status="scheduled", scheduled_at="2026-01-11T18:00:00Z")], now=NOW)
    session.expire_all()
    assert session.scalars(select(Match)).one().changed_at == NOW  # RF-159
    assert session.scalars(select(Season)).one().changed_at == NOW
    assert {"season", "events", "franchises", "matches"} <= report.changed_datasets
    assert dataset_times(session)["matches"] == NOW


def test_reingerir_lo_mismo_no_mueve_la_hora(session, ingest):
    records = [*base(), match(status="scheduled", scheduled_at="2026-01-11T18:00:00Z")]
    ingest(records, now=NOW)
    report = ingest(records, now=LATER)
    session.expire_all()
    assert session.scalars(select(Match)).one().changed_at == NOW
    assert report.changed_datasets == set()
    assert dataset_times(session)["matches"] == NOW


def test_un_valor_distinto_mueve_la_hora_de_la_fila_y_del_conjunto(session, ingest):
    ingest([*base(), match(status="live", maps_won=[0, 0])], now=NOW)
    report = ingest([match(hours=1, status="live", maps_won=[1, 0])], now=LATER)
    session.expire_all()
    assert session.scalars(select(Match)).one().changed_at == LATER
    # Un partido en vivo cambia también el conjunto de datos en vivo (RF-80).
    assert {"matches", "live"} <= report.changed_datasets
    assert dataset_times(session)["live"] == LATER


def test_un_horario_nuevo_cambia_la_hora_del_partido(session, ingest):
    ingest([*base(), match(status="scheduled", scheduled_at="2026-01-11T18:00:00Z")], now=NOW)
    ingest([match(hours=1, status="postponed", scheduled_at="2026-01-12T18:00:00Z")], now=LATER)
    session.expire_all()
    assert session.scalars(select(Match)).one().changed_at == LATER


def test_un_gamertag_anterior_nuevo_cambia_la_hora_del_jugador(session, ingest):
    from tests.integration.ingest.helpers import rec
    ingest([rec("player", "p1", gamertag="[FICTICIO] Nuevo")], now=NOW)
    ingest([rec("player", "p1", hours=1, gamertag="[FICTICIO] Nuevo", previous_gamertags=["[FICTICIO] Viejo"])], now=LATER)
    session.expire_all()
    assert session.scalars(select(Player)).one().changed_at == LATER


def test_quitar_todos_los_gamertags_anteriores_tambien_es_un_cambio(session, ingest):
    from tests.integration.ingest.helpers import rec
    ingest([rec("player", "p1", gamertag="[FICTICIO] Nuevo", previous_gamertags=["[FICTICIO] Viejo"])], now=NOW)
    report = ingest([rec("player", "p1", hours=1, gamertag="[FICTICIO] Nuevo", previous_gamertags=[])], now=LATER)
    session.expire_all()
    assert session.scalars(select(Player)).one().changed_at == LATER
    assert "players" in report.changed_datasets


def test_el_cambio_de_temporada_cambia_los_conjuntos_de_la_temporada(session, ingest):
    from tests.integration.ingest.helpers import rec
    ingest([*base(), match(status="finished", maps_won=[3, 0], winner_side=1)], now=NOW)
    report = ingest([rec("season", "s2027", year=2027, name="CDL 2027"),
                     rec("event", "ev27", season_year=2027, name="[FICTICIO] Major 2027"),
                     rec("match", "m27", event_ref="bp:ev27", best_of=5, status="live",
                         slots=[{"franchise_ref": "bp:t1"}, {"franchise_ref": "bp:t2"}])], now=LATER)
    assert {"season", "events", "matches", "standings", "players"} <= report.changed_datasets
