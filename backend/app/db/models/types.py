"""Tipos y valores cerrados compartidos por los modelos (plan de la spec 002, §3)."""

import uuid

from sqlalchemy import Enum, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import String, Uuid

from app.domain.vocabulary import (  # noqa: F401 — se reexportan para los modelos
    LINK_TYPES,
    MATCH_STATUSES,
    ORIGIN_OUTCOMES,
    PHASES,
    ROLES,
    SOURCES,
)


def closed_values(name: str, values: tuple[str, ...]) -> Enum:
    """Lista cerrada guardada como texto con una restricción CHECK.

    Se usa texto + CHECK en lugar de un tipo ENUM nativo de PostgreSQL porque es más
    sencillo de ampliar en una migración futura (p. ej. si la spec añade una fase).
    """
    return Enum(*values, name=name, native_enum=False, create_constraint=True, length=32)


def uuid_pk():
    """Clave primaria UUID generada por la aplicación: identificador interno estable (plan §2.3)."""
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def corrected_fields_column():
    """Lista de campos marcados como corregidos en la fila (RF-97, plan D-9)."""
    return mapped_column(ARRAY(String), nullable=False, server_default=text("'{}'"), default=list)
