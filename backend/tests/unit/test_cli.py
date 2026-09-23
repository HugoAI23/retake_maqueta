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
