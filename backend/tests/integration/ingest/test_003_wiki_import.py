"""T-097 · Orden `retake import-wiki-csv` (spec 003: RF-4 a RF-4c, RF-32, RF-113; plan I-26).

Importa los CSV en una sola transacción. Si falta un archivo o una columna, no se registra
ningún dato; el intento sí queda anotado en el registro (RF-4b).
"""

from datetime import UTC, datetime

from sqlalchemy import func, select, text

from app import cli
from app.curation.loader import Curation, parse_curation
from app.db.models import Championship, Placement, PlacementRoster, Player, SourceState, SyncRun
from app.ingest.store import entity_for
from app.ingest.wiki_import import import_wiki_csv
from app.sources import wiki_csv
from tests.unit.sources.test_wiki_csv import HISTORY_COLUMNS, folder, history_row, write  # noqa: F401

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
LEAGUE_TABLES = ("championship", "placement", "placement_roster", "franchise", "identity", "player", "observation")


def counts(session) -> dict:
    session.expire_all()
    return {t: session.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in LEAGUE_TABLES}


def runs(session):
    session.expire_all()
    return session.scalars(select(SyncRun).order_by(SyncRun.id)).all()


def test_importa_el_historial_y_los_datos_personales(session, folder):
    result = import_wiki_csv(session, folder, curation=Curation(), now=NOW)
    assert result.outcome == "success"
    assert session.scalar(select(func.count()).select_from(Championship)) == 2
    assert session.scalar(select(func.count()).select_from(Placement)) == 4
    assert session.scalar(select(func.count()).select_from(PlacementRoster)) == 5
    uno = session.get(Player, entity_for(session, "player", "wiki:[FICTICIO]_Uno"))
    assert (uno.real_name, str(uno.birth_date)) == ("[FICTICIO] Nombre Uno", "2000-01-02")


def test_importar_dos_veces_no_duplica_nada(session, folder):
    import_wiki_csv(session, folder, curation=Curation(), now=NOW)
    before = counts(session)
    result = import_wiki_csv(session, folder, curation=Curation(), now=NOW.replace(hour=13))
    assert result.outcome == "success"
    assert counts(session) == before


def test_queda_anotada_en_el_registro_y_como_ultima_importacion(session, folder):
    import_wiki_csv(session, folder, curation=Curation(), now=NOW)
    (run,) = runs(session)
    assert (run.source, run.job, run.outcome) == ("wiki", "history", "success")
    state = session.get(SourceState, ("wiki", "history"))
    assert state.last_success_at == NOW and state.last_attempt_at == NOW


def test_un_archivo_roto_no_registra_ningun_dato_pero_anota_el_fallo(session, folder):
    import_wiki_csv(session, folder, curation=Curation(), now=NOW)
    before = counts(session)
    write(folder / wiki_csv.HISTORY_FILE, ["Year", "Team"], [["2027", "[FICTICIO] Nuevo"]])
    result = import_wiki_csv(session, folder, curation=Curation(), now=NOW.replace(hour=13))
    assert result.outcome == "failure"
    assert wiki_csv.HISTORY_FILE in result.message
    assert counts(session) == before
    assert [r.outcome for r in runs(session)] == ["success", "failure"]
    assert session.get(SourceState, ("wiki", "history")).last_success_at == NOW


def test_una_fila_con_problemas_deja_la_importacion_parcial(session, folder):
    write(folder / wiki_csv.HISTORY_FILE, HISTORY_COLUMNS, [
        history_row("1", "2026", "[FICTICIO] Alfa", "[FICTICIO] Uno"),
        history_row("1", "dos mil", "[FICTICIO] Beta", "[FICTICIO] Tres"),
        history_row("2", "2026", "[FICTICIO] Beta", "[FICTICIO] Tres", prize="mucho"),
    ])
    result = import_wiki_csv(session, folder, curation=Curation(), now=NOW)
    assert result.outcome == "partial"
    assert any("dos mil" in incident for incident in result.incidents)
    assert any("prize_usd" in incident for incident in result.incidents)
    assert session.scalar(select(func.count()).select_from(Placement)) == 2


def test_respeta_la_retirada_de_datos_personales_de_la_curacion(session, folder):
    curation = parse_curation("personal_data_removals: [ {player: 'wiki:[FICTICIO]_Uno', requested_on: 2026-09-01} ]")
    import_wiki_csv(session, folder, curation=curation, now=NOW)
    uno = session.get(Player, entity_for(session, "player", "wiki:[FICTICIO]_Uno"))
    assert (uno.real_name, uno.birth_date, uno.personal_data_removed) == (None, None, True)


def test_la_orden_importa_desde_la_carpeta_indicada(session, folder, clean_db, monkeypatch, capsys):
    monkeypatch.setattr("app.db.engine.get_engine", lambda: clean_db)
    monkeypatch.setattr("app.ingest.wiki_import.load_curation", lambda *a, **k: Curation())
    cli.main(["import-wiki-csv", "--dir", str(folder)])
    out = capsys.readouterr().out
    assert "Resultado: success" in out and "clasificaciones: 4" in out
    assert session.scalar(select(func.count()).select_from(Placement)) == 4


def test_la_orden_con_un_archivo_que_falta_sale_con_codigo_1(folder, clean_db, monkeypatch, capsys):
    import pytest

    (folder / wiki_csv.BIRTHDAYS_FILE).unlink()
    monkeypatch.setattr("app.db.engine.get_engine", lambda: clean_db)
    monkeypatch.setattr("app.ingest.wiki_import.load_curation", lambda *a, **k: Curation())
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["import-wiki-csv", "--dir", str(folder)])
    assert exit_info.value.code == 1
    assert wiki_csv.BIRTHDAYS_FILE in capsys.readouterr().err
    with clean_db.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM championship")).scalar_one() == 0
