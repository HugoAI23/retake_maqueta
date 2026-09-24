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
