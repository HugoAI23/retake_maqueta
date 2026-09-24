"""Pruebas del comando `retake` (T-008)."""

import pytest

from app import cli


def test_sin_comando_muestra_error_de_uso():
    with pytest.raises(SystemExit):
        cli.main([])


def test_migrate_llama_a_alembic(monkeypatch):
    calls = []
    monkeypatch.setattr(cli.command, "upgrade", lambda config, revision: calls.append(revision))
    cli.main(["migrate"])
    assert calls == ["head"]


def test_apply_curation_con_error_sale_con_codigo_1(monkeypatch, capsys):
    from app.curation import loader

    def broken(*_args, **_kwargs):
        raise loader.CurationError("archivo roto")

    monkeypatch.setattr(loader, "load_curation", broken)
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["apply-curation"])
    assert exit_info.value.code == 1
    assert "archivo roto" in capsys.readouterr().err


def test_sync_once_bp(monkeypatch, capsys):
    from app.sources.contract import ConsultaResult

    dummy = ConsultaResult(source="bp", job="regular", outcome="success",
                          records=[{"kind": "season", "source": "bp", "source_id": "2026"}])
    monkeypatch.setattr("app.sources.bp.consult_regular", lambda client, now: dummy)
    cli.main(["sync-once", "--source", "bp"])
    out = capsys.readouterr().out
    assert "Resultado: success" in out
    assert "season: 1" in out


def test_sync_once_ya_no_admite_la_wiki():
    # Spec 003, C-18: la Wiki se importa con `retake import-wiki-csv` (I-26).
    with pytest.raises(SystemExit):
        cli.main(["sync-once", "--source", "wiki"])


def test_sync_command_invoca_worker(monkeypatch):
    called = []

    class DummyWorker:
        def run(self):
            called.append("run")

    monkeypatch.setattr("app.sync.worker.SyncWorker", lambda: DummyWorker())
    cli.main(["sync"])
    assert called == ["run"]


def test_source_mode_cli_invoca_command(monkeypatch):
    calls = []
    monkeypatch.setitem(cli.COMMANDS, "source-mode", (lambda mode: calls.append(mode), "help"))
    cli.main(["source-mode", "simulated"])
    assert calls == ["simulated"]



def test_sync_que_no_puede_arrancar_sale_con_un_mensaje_claro(monkeypatch, capsys):
    # RF-9 a RF-11: en modo fixtures (o en producción con datos ficticios) no arranca, sin traza de error.
    class Refusing:
        def run(self):
            raise RuntimeError("En modo fixtures los datos de la liga son los de prueba")

    monkeypatch.setattr("app.sync.worker.SyncWorker", lambda: Refusing())
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["sync"])
    assert exit_info.value.code == 1
    assert "modo fixtures" in capsys.readouterr().err


def test_source_mode_recuerda_volver_a_importar_la_wiki(monkeypatch, capsys):
    # RF-12 borra toda la liga, también el historial importado de los archivos de la Wiki (C-15, I-26).
    from types import SimpleNamespace

    monkeypatch.setattr("app.config.get_settings", lambda: SimpleNamespace(app_env="development"))
    monkeypatch.setattr("app.db.engine.get_engine", lambda: None)
    monkeypatch.setattr(cli, "set_source_mode", lambda session, mode, app_env: None)
    cli.main(["source-mode", "real"])
    assert "import-wiki-csv" in capsys.readouterr().out
