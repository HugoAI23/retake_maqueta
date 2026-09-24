"""Copias propias de los logos (plan de la spec 003, §2 y decisiones H-9, D-13 y D-14).

- Solo se aceptan PNG, JPEG o WebP que Pillow abre y verifica de verdad, no por su extensión:
  un SVG u otro formato que pueda llevar código se rechaza (RF-68).
- Como máximo 1 MB; lo que pase de ahí se rechaza sin intentar abrirlo (RF-69).
- Cada copia se identifica por la huella SHA-256 de su contenido: una imagen idéntica se guarda
  una sola vez aunque llegue de direcciones distintas (RF-66, D-13).
- Un logo no válido o imposible de descargar se trata como logo no registrado (RF-70).
"""

import hashlib
import io
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.db.models import LogoImage
from app.domain.vocabulary import LOGO_MAX_BYTES
from app.sources.http import PoliteClient, SourceUnavailable, Transport

# Formato que detecta Pillow → tipo de imagen que se sirve (RF-68).
FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


class InvalidLogo(Exception):
    """El logo no es una imagen admitida o no se ha podido descargar (RF-70)."""


@dataclass(frozen=True)
class LogoInfo:
    media_type: str
    width: int
    height: int
    size_bytes: int


def fingerprint(content: bytes) -> str:
    """Huella SHA-256 del contenido: el identificador de la copia (D-13)."""
    return hashlib.sha256(content).hexdigest()


def validate_logo(content: bytes) -> LogoInfo:
    """Comprueba que el contenido es un PNG, JPEG o WebP real de 1 MB como máximo.

    Raises:
        InvalidLogo: con el motivo (vacío, demasiado grande, no es una imagen o formato no admitido).
    """
    if not content:
        raise InvalidLogo("archivo vacío")
    if len(content) > LOGO_MAX_BYTES:
        raise InvalidLogo(f"ocupa {len(content)} bytes: el máximo es 1 MB")
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()  # detecta archivos corruptos o manipulados
        with Image.open(io.BytesIO(content)) as image:  # verify() inutiliza la imagen: se vuelve a abrir
            fmt, (width, height) = image.format, image.size
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise InvalidLogo(f"no es una imagen válida ({type(error).__name__})") from None
    if fmt not in FORMATS:
        raise InvalidLogo(f"formato no admitido: {fmt}")
    return LogoInfo(FORMATS[fmt], width, height, len(content))


def download_logo(url: str, transport: Transport, *, clock, sleep, source: str = "bp") -> bytes:
    """Descarga un logo con el cliente educado de su propio servidor (identificación y pausa).

    Raises:
        InvalidLogo: si la dirección no es `https` o la descarga falla.
    """
    parts = urlsplit(str(url))
    if parts.scheme != "https" or not parts.netloc:
        raise InvalidLogo("solo se descargan logos por https")
    client = PoliteClient(source, transport, clock=clock, sleep=sleep, base_url=f"https://{parts.netloc}")
    try:
        response = client.get(url)
    except SourceUnavailable as error:
        raise InvalidLogo(f"no se pudo descargar: {error}") from None
    return bytes(response.content)


def store_logo(session: Session, content: bytes, now: datetime) -> str:
    """Valida y guarda la copia si no existe ya; devuelve su identificador (huella).

    Raises:
        InvalidLogo: si no es una imagen admitida (no se guarda nada).
    """
    info = validate_logo(content)
    logo_id = fingerprint(content)
    if session.get(LogoImage, logo_id) is None:
        session.add(LogoImage(id=logo_id, content=content, media_type=info.media_type, size_bytes=info.size_bytes,
                              width=info.width, height=info.height, first_seen_at=now))
        session.flush()
    return logo_id
