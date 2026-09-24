"""T-034 · Copia propia de los logos en la base de datos, sin duplicados (RF-65, RF-66, H-9)."""

import io
from datetime import UTC, datetime

from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import LogoImage
from app.logos import InvalidLogo, download_logo, store_logo
from tests.unit.sources.fakes import FakeResponse, FakeTransport, SteppingClock

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
LOGO_URL = "https://dfpiiufxcciujugzjvgx.supabase.co/storage/v1/object/public/teams/TX.webp"


def webp() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (147, 200, 82)).save(buffer, format="WEBP")
    return buffer.getvalue()


def test_dos_descargas_identicas_se_guardan_una_sola_vez(clean_db):
    content = webp()
    with Session(clean_db) as session:
        first = store_logo(session, content, NOW)
        second = store_logo(session, content, NOW)
        session.commit()
        assert first == second
        assert session.scalar(select(func.count()).select_from(LogoImage)) == 1
        stored = session.get(LogoImage, first)
        assert (stored.media_type, stored.width, stored.content) == ("image/webp", 8, content)


def test_un_logo_no_valido_no_se_guarda(clean_db):
    with Session(clean_db) as session:
        try:
            store_logo(session, b"<svg/>", NOW)
        except InvalidLogo:
            pass
        assert session.scalar(select(func.count()).select_from(LogoImage)) == 0


def test_descarga_con_el_cliente_educado_de_su_servidor():
    clock = SteppingClock()
    response = FakeResponse(200, "")
    response.content = webp()
    transport = FakeTransport({"https://dfpiiufxcciujugzjvgx.supabase.co/robots.txt": FakeResponse(404), LOGO_URL: response}, clock)
    assert download_logo(LOGO_URL, transport, clock=clock, sleep=clock.sleep) == response.content
    assert transport.calls[-1]["headers"]["User-Agent"].startswith("Retake/")


def test_una_direccion_que_no_es_https_no_se_descarga():
    clock = SteppingClock()
    transport = FakeTransport({}, clock)
    try:
        download_logo("http://ejemplo.com/logo.png", transport, clock=clock, sleep=clock.sleep)
        raise AssertionError("debía rechazarse")
    except InvalidLogo as error:
        assert "https" in str(error)
    assert transport.calls == []
