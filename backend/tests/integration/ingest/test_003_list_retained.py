"""T-047 · Orden `retake list-retained` (spec 003: RF-54, RF-56; plan §3.5).

Lista los registros retenidos y sugiere candidatos parecidos (mismo gamertag, mismo nombre, o
mismos equipos y fecha). Solo sugiere: nunca une nada ni cambia ningún dato.
"""

from datetime import UTC, datetime

from sqlalchemy import inspect, text

from app import cli
from app.curation.retained import list_retained
from tests.integration.ingest.helpers import rec, team
from tests.integration.ingest.test_matches import base, match

NOW = datetime(2026, 1, 11, 12, 0, tzinfo=UTC)


def world():
    return [
        *base(),
        match(status="scheduled", scheduled_at="2026-01-11T18:00:00Z",
              slots=[{"franchise_ref": "bp:t1"}, {"franchise_ref": "bp:t2"}]),
        rec("player", "p1", gamertag="[FICTICIO] Uno"),
        rec("player", "Uno", source="wiki", gamertag="[FICTICIO] UNO"),
        rec("player", "Nadie", source="wiki", gamertag="[FICTICIO] Sin parecido"),
        *team("Uno_Wiki", "[FICTICIO] Uno", source="wiki"),
        *team("Dos_Wiki", "[FICTICIO] Dos", source="wiki"),
        rec("match", "M1", source="wiki", event_ref="bp:ev1", best_of=5, status="scheduled",
            scheduled_at="2026-01-11T21:00:00Z", slots=[{"franchise_ref": "wiki:Dos_Wiki"}, {"franchise_ref": "wiki:Uno_Wiki"}]),
    ]


def dump(engine) -> dict:
    """Todas las filas de todas las tablas, para comprobar que nada cambia."""
    with engine.connect() as connection:
        return {table: sorted(map(repr, connection.execute(text(f'SELECT * FROM "{table}"')).all()))
                for table in inspect(engine).get_table_names()}


def test_sugiere_candidatos_parecidos(session, ingest):
    ingest(world(), now=NOW)
    items = {item.ref: item for item in list_retained(session)}
    assert set(items) == {"wiki:Uno", "wiki:Nadie", "wiki:Uno_Wiki", "wiki:Dos_Wiki", "wiki:M1"}
    assert items["wiki:Uno"].kind == "player"
    assert items["wiki:Uno"].since == NOW
    assert [c.ref for c in items["wiki:Uno"].candidates] == ["bp:p1"]        # mismo gamertag, sin mayúsculas
    assert items["wiki:Nadie"].candidates == []
    assert [c.ref for c in items["wiki:Uno_Wiki"].candidates] == ["bp:t1"]   # mismo nombre
    assert [c.ref for c in items["wiki:M1"].candidates] == ["bp:m1"]         # mismos equipos y fecha


def test_la_orden_lista_y_no_cambia_ningun_dato(session, ingest, clean_db, monkeypatch, capsys):
    ingest(world(), now=NOW)
    before = dump(clean_db)
    monkeypatch.setattr("app.db.engine.get_engine", lambda: clean_db)
    cli.main(["list-retained"])
    out = capsys.readouterr().out
    assert "wiki:Uno" in out and "bp:p1" in out
    assert "nunca une nada" in out
    assert dump(clean_db) == before
