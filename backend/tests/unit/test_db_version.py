"""Pruebas de la comprobación de versión de PostgreSQL (T-004)."""

import pytest

from app.db.session import UnsupportedDatabaseError, check_server_version, ensure_supported_version


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class FakeConnection:
    """Servidor simulado que responde con una versión fija."""

    def __init__(self, version_num):
        self.version_num = version_num

    def execute(self, _statement):
        return FakeResult(str(self.version_num))


def test_postgresql_14_se_rechaza_con_un_mensaje_claro():
    with pytest.raises(UnsupportedDatabaseError, match="PostgreSQL 14 no es compatible"):
        check_server_version(FakeConnection(140020))


def test_postgresql_18_se_acepta():
    assert check_server_version(FakeConnection(180004)) == 180004


@pytest.mark.parametrize("version_num", [170009, 179999])
def test_versiones_anteriores_a_18_se_rechazan(version_num):
    with pytest.raises(UnsupportedDatabaseError):
        ensure_supported_version(version_num)
