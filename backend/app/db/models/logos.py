"""Copias propias de los logos (plan de la spec 003, §4 y decisiones H-9 y D-13)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.types import LOGO_MAX_BYTES, LOGO_MEDIA_TYPES, closed_values


class LogoImage(Base):
    """Copia de un logo descargado de una fuente, ya verificado como imagen (RF-65 a RF-70).

    - `id` es la huella SHA-256 del contenido: una imagen idéntica se guarda una sola
      vez aunque llegue de direcciones distintas (RF-66, plan D-13).
    - Solo se admiten PNG, JPEG y WebP, formatos que no pueden contener código (RF-68),
      de 1 MB como máximo (RF-69). La base de datos lo exige además de la validación.
    """

    __tablename__ = "logo_image"
    __table_args__ = (
        CheckConstraint(f"size_bytes > 0 AND size_bytes <= {LOGO_MAX_BYTES}", name="size_range"),
        CheckConstraint("width > 0 AND height > 0", name="dimensions_positive"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    media_type: Mapped[str] = mapped_column(closed_values("media_type", LOGO_MEDIA_TYPES))
    size_bytes: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
