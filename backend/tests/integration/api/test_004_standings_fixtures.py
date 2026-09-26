"""T-008 de la spec 004 · Balance de `/api/standings` con los datos de prueba compartidos (RF-45)."""

from tests.integration.api.test_read_api import get


def test_balance_de_la_tabla_con_los_datos_de_prueba(api):
    rows = {row["identity"]["shortName"]: (row["series"], row["maps"]) for row in get(api, "/api/standings")}
    record = lambda won, lost: {"won": won, "lost": lost}  # noqa: E731
    # Tres partidos finalizados entre A y B (uno de ellos, por incomparecencia con marcador) y la
    # gran final de 2026. El partido en vivo no cuenta; sus equipos no están en la tabla.
    assert rows.pop("[FICTICIO] Equipo A") == (record(3, 0), record(8, 0))
    assert rows.pop("[FICTICIO] Equipo B") == (record(0, 3), record(0, 8))
    assert rows.pop("FaZe VGS") == (record(1, 0), record(5, 2))
    assert rows.pop("OpTic TEX") == (record(0, 1), record(2, 5))
    assert len(rows) == 10
    assert all(value == (record(0, 0), record(0, 0)) for value in rows.values())
