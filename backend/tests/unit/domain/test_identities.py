"""T-024 y T-025 · Identidades (RF-11 a RF-13, RF-73, RF-74, RF-121, RF-124)."""

from datetime import UTC, date, datetime, timedelta

from app.domain.identities import (
    IdentityData,
    IdentityVersion,
    identity_at,
    identity_for_championship,
    identity_valid_from,
    needs_new_identity,
)

BASE = IdentityData("[FICTICIO] Equipo", "FEQ", "https://x.test/a.png", "#112233", "#445566")


def test_cambiar_solo_el_color_secundario_crea_una_identidad_nueva():
    changed = IdentityData(*BASE[:4], "#000000")
    assert needs_new_identity(BASE, changed)


def test_repetir_los_mismos_cinco_datos_no_crea_identidad():
    assert not needs_new_identity(BASE, IdentityData(*BASE))


def test_la_primera_identidad_siempre_es_nueva():
    assert needs_new_identity(None, BASE)


def test_valid_from_es_la_fecha_publicada_o_el_instante_de_observacion():
    published = datetime(2026, 1, 1, tzinfo=UTC)
    observed = datetime(2026, 3, 1, tzinfo=UTC)
    assert identity_valid_from(published, observed) == published
    assert identity_valid_from(None, observed) == observed


CHANGE = datetime(2026, 5, 10, 15, 0, tzinfo=UTC)
OLD = IdentityVersion("old", BASE, datetime(2020, 1, 1, tzinfo=UTC))
NEW = IdentityVersion("new", IdentityData("[FICTICIO] Nuevo", "FNU", None, "#ffffff", None), CHANGE)


def test_identidad_de_un_partido_segun_su_hora_de_inicio():
    assert identity_at([OLD, NEW], CHANGE - timedelta(hours=1)).id == "old"
    assert identity_at([OLD, NEW], CHANGE + timedelta(hours=1)).id == "new"
    assert identity_at([NEW, OLD], CHANGE).id == "new"


def test_antes_de_la_primera_identidad_conocida_se_usa_la_primera():
    assert identity_at([OLD, NEW], datetime(2019, 1, 1, tzinfo=UTC)).id == "old"


def test_sin_identidades_no_hay_identidad():
    assert identity_at([], CHANGE) is None


def test_campeonato_con_fecha_de_final_usa_la_vigente_ese_dia():
    assert identity_for_championship([OLD, NEW], date(2026, 5, 9), "cualquiera", 2026).id == "old"
    # Un cambio el mismo día de la final cuenta: la final se jugó ese día.
    assert identity_for_championship([OLD, NEW], date(2026, 5, 10), "cualquiera", 2026).id == "new"


def test_campeonato_sin_fecha_usa_la_que_coincide_por_nombre_publicado():
    assert identity_for_championship([OLD, NEW], None, "[FICTICIO] Equipo", 2026).id == "old"
    assert identity_for_championship([OLD, NEW], None, "  [ficticio] nuevo ", 2026).id == "new"


def test_campeonato_sin_fecha_ni_coincidencia_usa_la_vigente_el_31_de_diciembre():
    assert identity_for_championship([OLD, NEW], None, "Otro nombre", 2025).id == "old"
    assert identity_for_championship([OLD, NEW], None, None, 2026).id == "new"
