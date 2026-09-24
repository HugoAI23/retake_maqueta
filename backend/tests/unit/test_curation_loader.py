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


def test_cada_modo_usa_su_archivo_de_curacion():
    # Plan I-35: los datos de prueba tienen su propia curación; la real no las mezcla.
    from app.curation.loader import CURATION_PATH, FIXTURES_CURATION_PATH, curation_path

    assert curation_path("fixtures") == FIXTURES_CURATION_PATH
    assert curation_path("real") == CURATION_PATH
    assert curation_path("simulated") == CURATION_PATH
    assert FIXTURES_CURATION_PATH != CURATION_PATH


def _entries(curation):
    return [*curation.roles, *curation.player_merges, *curation.player_splits, *curation.merges, *curation.confirmed_new]


def test_la_curacion_real_no_lleva_entradas_de_prueba_ni_la_de_prueba_reales():
    # Cada archivo se valida en modo estricto contra su base: una entrada del otro la haría fallar (I-35).
    from app.curation.loader import CURATION_PATH, FIXTURES_CURATION_PATH

    real, fixtures = load_curation(CURATION_PATH), load_curation(FIXTURES_CURATION_PATH)
    assert not any("[FICTICIO]" in entry.reason for entry in _entries(real))
    assert not any("fx-" in str(entry.player) for entry in real.personal_data_removals)
    assert _entries(fixtures) and all(entry.reason.startswith("[FICTICIO]") for entry in _entries(fixtures))
    assert fixtures.countries == {}
