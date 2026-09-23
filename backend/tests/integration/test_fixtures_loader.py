"""T-043 · Comando de carga de datos de prueba."""

import json

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.curation.loader import Curation
from app.db.models import Player
from app.ingest.fixtures import FixtureError, load_fixtures, read_fixture_files

REAL = {
    "consulted": [{"source": "wiki", "url": "https://example.test/page", "date": "2026-09-22"}],
    "records": [{"kind": "player", "source": "wiki", "source_id": "Real", "observed_at": "2026-09-22T00:00:00Z",
                 "gamertag": "Real"}],
}
FICTIONAL = {
    "description": "Caso de prueba",
    "records": [{"kind": "player", "source": "bp", "source_id": "f1", "observed_at": "2026-09-22T00:00:00Z",
                 "gamertag": "[FICTICIO] Uno", "fictional": True}],
}


@pytest.fixture
def fixtures_dir(tmp_path):
    (tmp_path / "real").mkdir()
    (tmp_path / "fictional").mkdir()
    (tmp_path / "real" / "01_players.json").write_text(json.dumps(REAL), encoding="utf-8")
    (tmp_path / "fictional" / "01_players.json").write_text(json.dumps(FICTIONAL), encoding="utf-8")
    return tmp_path


def test_carga_completa_en_entorno_de_pruebas(clean_db, fixtures_dir):
    with Session(clean_db) as session:
        result = load_fixtures(session, app_env="test", directory=fixtures_dir, curation=Curation())
        session.commit()
        assert result.report.accepted == 2
        assert result.report.rejected == []
        assert session.scalar(select(func.count()).select_from(Player)) == 2


def test_en_produccion_se_niega_a_cargar_datos_ficticios_sin_tocar_nada(clean_db, fixtures_dir):
    with Session(clean_db) as session:
        with pytest.raises(FixtureError, match="producción"):
            load_fixtures(session, app_env="production", directory=fixtures_dir, curation=Curation())
        assert session.scalar(select(func.count()).select_from(Player)) == 0


def test_la_muestra_real_va_antes_que_la_ficticia(fixtures_dir):
    files = read_fixture_files(fixtures_dir)
    assert [f.path.parent.name for f in files] == ["real", "fictional"]


def test_un_archivo_real_debe_indicar_sus_fuentes(fixtures_dir):
    (fixtures_dir / "real" / "02_bad.json").write_text(json.dumps({"records": []}), encoding="utf-8")
    with pytest.raises(FixtureError, match="consulted"):
        read_fixture_files(fixtures_dir)


def test_un_registro_ficticio_en_la_muestra_real_es_un_error(fixtures_dir):
    bad = {**REAL, "records": [{**REAL["records"][0], "fictional": True}]}
    (fixtures_dir / "real" / "02_bad.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(FixtureError, match="ficticio"):
        read_fixture_files(fixtures_dir)


def test_un_registro_sin_marca_en_la_carpeta_ficticia_es_un_error(fixtures_dir):
    bad = {**FICTIONAL, "records": [{**FICTIONAL["records"][0], "fictional": False}]}
    (fixtures_dir / "fictional" / "02_bad.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(FixtureError, match="fictional"):
        read_fixture_files(fixtures_dir)
