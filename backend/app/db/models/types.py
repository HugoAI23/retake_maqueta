"""Tipos y valores cerrados compartidos por los modelos (plan de la spec 002, §3)."""

import uuid

from sqlalchemy import DateTime, Enum, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import String, Uuid

from app.domain.vocabulary import (  # noqa: F401 — se reexportan para los modelos
    DATASETS,
    INCIDENT_KINDS,
    INVALID_REASONS,
    LINK_TYPES,
    LOGO_MAX_BYTES,
    LOGO_MEDIA_TYPES,
    MATCH_STATUSES,
    ORIGIN_OUTCOMES,
    PHASES,
    REQUEST_KINDS,
    REQUEST_RESULTS,
    REQUEST_STATUSES,
    ROLES,
    RUN_OUTCOMES,
    SOURCES,
    SYNC_JOBS,
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


def changed_at_column():
    """Instante en que cambió por última vez el valor resuelto de la fila (spec 003, RF-157).

    Nulo en las filas anteriores a la spec 003: no se inventa cuándo cambiaron.
    """
    return mapped_column(DateTime(timezone=True))
