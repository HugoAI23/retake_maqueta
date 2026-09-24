"""T-034 · Logos: solo imágenes PNG, JPEG o WebP reales de 1 MB como máximo (RF-65 a RF-70)."""

import hashlib
import io

import pytest
from PIL import Image

from app.logos import InvalidLogo, fingerprint, validate_logo


def image_bytes(fmt: str, size=(4, 3)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (228, 61, 48)).save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.mark.parametrize(("fmt", "media_type"), [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
def test_acepta_png_jpeg_y_webp(fmt, media_type):
    content = image_bytes(fmt)
    info = validate_logo(content)
    assert (info.media_type, info.width, info.height, info.size_bytes) == (media_type, 4, 3, len(content))


def test_rechaza_un_svg_porque_puede_contener_codigo():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    with pytest.raises(InvalidLogo, match="no es una imagen"):
        validate_logo(svg)


def test_rechaza_un_gif():
    with pytest.raises(InvalidLogo, match="formato no admitido: GIF"):
        validate_logo(image_bytes("GIF"))


def test_rechaza_un_falso_png():
    fake = b"\x89PNG\r\n\x1a\n" + b"esto no es una imagen" * 10
    with pytest.raises(InvalidLogo):
        validate_logo(fake)


def test_rechaza_mas_de_un_mega_sin_intentar_abrirlo():
    with pytest.raises(InvalidLogo, match="1 MB"):
        validate_logo(b"\x89PNG" + b"0" * 1_048_576)


def test_rechaza_un_archivo_vacio():
    with pytest.raises(InvalidLogo):
        validate_logo(b"")


def test_huella_sha256_del_contenido():
    content = image_bytes("PNG")
    assert fingerprint(content) == hashlib.sha256(content).hexdigest()
    # Dos descargas idénticas tienen la misma huella: se guardan una sola vez (RF-66).
    assert fingerprint(image_bytes("PNG")) == fingerprint(content)
