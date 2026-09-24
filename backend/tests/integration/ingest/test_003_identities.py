"""T-042 · Identidad combinada entre fuentes y copia propia de los logos.

Spec 003: RF-61 a RF-65 (identidad combinada campo a campo; Q-45: la fecha de vigencia es un
campo más) y RF-65 a RF-71 (copia del logo, sin duplicados, imagen nueva en la misma dirección,
logo no válido y logo que se deja de publicar). Sustituye el ajuste I-15 de la 002.
"""

import io
from datetime import UTC, datetime

from PIL import Image
from sqlalchemy import func, select

from app.db.models import Identity, LogoImage
from app.logos import InvalidLogo, fingerprint
from tests.integration.ingest.helpers import rec, team

LOGO = "https://ejemplo.com/logo.png"


def png(color=(228, 61, 48)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), color).save(buffer, format="PNG")
    return buffer.getvalue()


class FakeFetcher:
    """Descargador de logos de prueba: devuelve la imagen asignada a cada dirección."""

    def __init__(self, images):
        self.images = dict(images)
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        image = self.images.get(url)
        if image is None:
            raise InvalidLogo(f"no se ha podido obtener {url}")
        return image


def identities(session):
    session.expire_all()
    return session.scalars(select(Identity).order_by(Identity.valid_from)).all()


def wiki_team(hours=0, **identity):
    return [rec("franchise", "Team", source="wiki", hours=hours, same_as=["bp:t1"]),
            rec("identity", "Team-id", source="wiki", hours=hours, franchise_ref="wiki:Team", **identity)]


# --- Identidad combinada (RF-61 a RF-63) --------------------------------------------------------


def test_dos_fuentes_con_identidades_distintas_dan_una_sola_identidad_combinada(session, ingest):
    ingest([*team("t1", "[FICTICIO] Equipo", abbreviation="FEQ", primary_color="#112233"),
            *wiki_team(hours=1, short_name="[FICTICIO] Equipo Wiki", abbreviation="FEW", secondary_color="#ffffff")])
    (identity,) = identities(session)
    assert (identity.short_name, identity.abbreviation, identity.primary_color, identity.secondary_color) == (
        "[FICTICIO] Equipo", "FEQ", "#112233", "#ffffff")


def test_el_orden_de_llegada_de_las_fuentes_no_cambia_el_resultado(session, ingest):
    ingest([rec("franchise", "t1"),
            *wiki_team(short_name="[FICTICIO] Equipo Wiki", abbreviation="FEW", secondary_color="#ffffff")])
    ingest([rec("identity", "t1-id", hours=1, franchise_ref="bp:t1", short_name="[FICTICIO] Equipo",
                abbreviation="FEQ", primary_color="#112233")])
    (identity,) = identities(session)
    assert (identity.short_name, identity.abbreviation, identity.primary_color, identity.secondary_color) == (
        "[FICTICIO] Equipo", "FEQ", "#112233", "#ffffff")


def test_la_fecha_de_vigencia_sale_de_la_fuente_con_mas_prioridad_que_la_publica(session, ingest):
    ingest([*team("t1", "[FICTICIO] Equipo"),
            *wiki_team(hours=1, short_name="[FICTICIO] Equipo", valid_from="2025-12-01T00:00:00Z")])
    (identity,) = identities(session)
    assert identity.valid_from == datetime(2025, 12, 1, tzinfo=UTC)  # BreakingPoint no publica la fecha (Q-45)


def test_un_cambio_real_tras_combinar_crea_una_identidad_nueva(session, ingest):
    ingest([*team("t1", "[FICTICIO] Equipo", abbreviation="FEQ"),
            *wiki_team(hours=1, short_name="[FICTICIO] Equipo", secondary_color="#ffffff")])
    ingest(team("t1", "[FICTICIO] Equipo Renovado", hours=5, abbreviation="FER"))
    old, new = identities(session)
    assert (old.short_name, new.short_name, new.abbreviation) == ("[FICTICIO] Equipo", "[FICTICIO] Equipo Renovado", "FER")
    assert new.secondary_color == "#ffffff"  # la Wiki sigue completando el campo que BreakingPoint no publica
    assert new.valid_from == datetime(2026, 1, 10, 17, 0, tzinfo=UTC)


def test_reingerir_las_dos_fuentes_sin_cambios_no_crea_identidades(session, ingest):
    records = [*team("t1", "[FICTICIO] Equipo", abbreviation="FEQ"),
               *wiki_team(hours=1, short_name="[FICTICIO] Equipo", secondary_color="#ffffff")]
    ingest(records)
    ingest(records)
    assert len(identities(session)) == 1


def test_una_identidad_anterior_de_una_fuente_no_se_combina_con_la_actual(session, ingest):
    # Se combina la identidad más reciente de cada fuente (la vigente para esa fuente); las
    # anteriores siguen siendo historial.
    ingest([*team("t1", "[FICTICIO] Equipo", abbreviation="FEQ"),
            rec("franchise", "Team", source="wiki", same_as=["bp:t1"]),
            rec("identity", "Team-2019", source="wiki", franchise_ref="wiki:Team",
                short_name="[FICTICIO] Nombre de 2019", valid_from="2019-01-01T00:00:00Z"),
            rec("identity", "Team-2026", source="wiki", hours=1, franchise_ref="wiki:Team",
                short_name="[FICTICIO] Equipo", secondary_color="#ffffff", valid_from="2025-12-01T00:00:00Z")])
    old, current = identities(session)
    assert (old.short_name, old.abbreviation, old.valid_from) == ("[FICTICIO] Nombre de 2019", None, datetime(2019, 1, 1, tzinfo=UTC))
    assert (current.short_name, current.abbreviation, current.secondary_color) == ("[FICTICIO] Equipo", "FEQ", "#ffffff")
    assert current.valid_from == datetime(2025, 12, 1, tzinfo=UTC)


# --- Copia propia de los logos (RF-65 a RF-71) --------------------------------------------------


def test_el_logo_se_copia_y_una_imagen_identica_se_guarda_una_vez(session, ingest):
    fetcher = FakeFetcher({LOGO: png(), "https://otra.com/logo.png": png()})
    ingest([*team("t1", "[FICTICIO] Uno", logo_url=LOGO), *team("t2", "[FICTICIO] Dos", logo_url="https://otra.com/logo.png")],
           logo_fetcher=fetcher)
    assert {i.logo_image_id for i in identities(session)} == {fingerprint(png())}
    assert session.scalar(select(func.count()).select_from(LogoImage)) == 1


def test_una_imagen_nueva_en_la_misma_direccion_es_un_logo_nuevo(session, ingest):
    ingest(team("t1", "[FICTICIO] Uno", logo_url=LOGO), logo_fetcher=FakeFetcher({LOGO: png()}))
    ingest(team("t1", "[FICTICIO] Uno", hours=2, logo_url=LOGO), logo_fetcher=FakeFetcher({LOGO: png((0, 0, 0))}))
    old, new = identities(session)
    assert (old.logo_image_id, new.logo_image_id) == (fingerprint(png()), fingerprint(png((0, 0, 0))))


def test_un_logo_que_no_se_puede_obtener_queda_sin_copia(session, ingest):
    ingest(team("t1", "[FICTICIO] Uno", logo_url=LOGO), logo_fetcher=FakeFetcher({LOGO: b"<svg/>"}))
    assert identities(session)[0].logo_image_id is None


def test_se_conserva_la_copia_si_la_fuente_deja_de_publicar_el_logo_o_falla_la_descarga(session, ingest):
    ingest(team("t1", "[FICTICIO] Uno", logo_url=LOGO), logo_fetcher=FakeFetcher({LOGO: png()}))
    ingest(team("t1", "[FICTICIO] Uno", hours=1), logo_fetcher=FakeFetcher({}))
    ingest(team("t1", "[FICTICIO] Uno", hours=2, logo_url=LOGO), logo_fetcher=FakeFetcher({}))
    (identity,) = identities(session)
    assert (identity.logo_url, identity.logo_image_id) == (LOGO, fingerprint(png()))


def test_sin_descargador_no_se_descarga_nada(session, ingest):
    ingest(team("t1", "[FICTICIO] Uno", logo_url=LOGO))
    assert identities(session)[0].logo_image_id is None


def test_cada_direccion_se_descarga_una_sola_vez_por_ingesta(session, ingest):
    # Los logos se revisan en el ciclo horario de identidades (plan §3.5); dentro de una ingesta,
    # una dirección repetida no se vuelve a pedir.
    fetcher = FakeFetcher({LOGO: png()})
    ingest([*team("t1", "[FICTICIO] Uno", logo_url=LOGO), *team("t2", "[FICTICIO] Dos", logo_url=LOGO)], logo_fetcher=fetcher)
    assert fetcher.calls == [LOGO]
