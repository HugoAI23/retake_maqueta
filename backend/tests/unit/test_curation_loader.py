"""T-039 · Lectura del archivo de curación."""

import pytest

from app.curation.loader import CurationError, load_curation, parse_curation


def test_un_archivo_valido(tmp_path):
    path = tmp_path / "curation.yaml"
    path.write_text(
        """
roles:
  - {player: "bp:1", role: SMG, reason: "Rol habitual en 2026"}
player_merges:
  - {players: ["bp:1", "wiki:Uno"], reason: "Misma persona"}
player_splits:
  - {players: ["bp:2", "wiki:Dos"], reason: "Personas distintas"}
personal_data_removals:
  - {player: "bp:3", requested_on: 2026-09-01}
""",
        encoding="utf-8",
    )
    curation = load_curation(path)
    assert curation.roles[0].role == "SMG"
    assert str(curation.player_merges[0].players[1]) == "wiki:Uno"
    assert str(curation.personal_data_removals[0].requested_on) == "2026-09-01"


def test_un_archivo_vacio_o_inexistente_es_una_curacion_vacia(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    assert load_curation(empty).roles == []
    assert load_curation(tmp_path / "no-existe.yaml").roles == []


@pytest.mark.parametrize(
    "content",
    [
        "roles: [ {player: 'bp:1', role: SMG} ]",  # sin motivo
        "roles: [ {player: 'bp:1', role: Flex, reason: 'x'} ]",  # rol no admitido
        "player_splits: [ {players: ['bp:1'], reason: 'x'} ]",  # separación de un solo jugador
        "roles: [",  # YAML roto
        "otra_seccion: []",
    ],
)
def test_un_archivo_mal_formado_da_un_error_claro(content):
    with pytest.raises(CurationError):
        parse_curation(content)
