"""Tablas de entrada (plan de la spec 002, §3.1).

Guardan lo que dice cada fuente por separado, para poder calcular el valor resuelto
con la prioridad entre fuentes y detectar correcciones (plan D-2).
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.db.models.types import LINK_TYPES, SOURCES, closed_values


class ExternalRef(Base):
    """Referencia externa: un objeto tal como lo identifica una fuente (`source` + `source_id`).

    `entity_id` apunta a la entidad interna a la que pertenece (jugador, franquicia,
    partido…) una vez agrupada con las demás referencias de la misma entidad.
    """

    __tablename__ = "external_ref"
    __table_args__ = (UniqueConstraint("kind", "source", "source_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(closed_values("source", SOURCES))
    source_id: Mapped[str] = mapped_column(String(255))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    fictional: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)


class RefLink(Base):
    """Enlace entre dos referencias externas declarado por una fuente (RF-114, RF-131)."""

    __tablename__ = "ref_link"
    __table_args__ = (UniqueConstraint("from_ref_id", "to_ref_id", "link_type"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    from_ref_id: Mapped[int] = mapped_column(ForeignKey("external_ref.id", ondelete="CASCADE"))
    to_ref_id: Mapped[int] = mapped_column(ForeignKey("external_ref.id", ondelete="CASCADE"))
    link_type: Mapped[str] = mapped_column(closed_values("link_type", LINK_TYPES))


class Observation(Base):
    """Último valor que una fuente ha publicado para un campo de una referencia externa.

    Se guardan también los valores no válidos (`is_valid = false`), para saber que el
    dato "ya había llegado" aunque se descartara (RF-98, RF-100). Un valor nulo en
    `value` significa que la fuente lo publica como ausente; si el campo nunca llegó,
    no hay fila (RF-65).
    """

    __tablename__ = "observation"
    __table_args__ = (UniqueConstraint("ref_id", "field"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ref_id: Mapped[int] = mapped_column(ForeignKey("external_ref.id", ondelete="CASCADE"))
    field: Mapped[str] = mapped_column(String(64))
    value: Mapped[object | None] = mapped_column(JSONB(none_as_null=True))
    is_valid: Mapped[bool] = mapped_column(Boolean)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
