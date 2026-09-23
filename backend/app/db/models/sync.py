"""Obtención automática: estado de las fuentes, tareas, peticiones, registro y resúmenes.

Plan de la spec 003, §4. Solo el proceso de obtención (`retake sync`) escribe en estas
tablas, salvo `sync_request`, donde la API apunta las peticiones del administrador (D-4).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.types import (
    DATASETS,
    INCIDENT_KINDS,
    REQUEST_KINDS,
    REQUEST_RESULTS,
    REQUEST_STATUSES,
    RUN_OUTCOMES,
    SOURCES,
    SYNC_JOBS,
    closed_values,
    uuid_pk,
)

# Longitud máxima de un mensaje de una fuente (RF-120).
MESSAGE_MAX_LENGTH = 500


class DatasetChange(Base):
    """Último cambio de cada conjunto de datos (plan D-7).

    Da la hora de última actualización de un bloque vacío (RF-158) y la de `/api/freshness`.
    """

    __tablename__ = "dataset_change"

    dataset: Mapped[str] = mapped_column(closed_values("dataset", DATASETS), primary_key=True)
    last_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceState(Base):
    """Estado de cada tipo de consulta de una fuente (RF-112 a RF-114).

    - `last_attempt_at` y `last_success_at` alimentan la página de administración y la
      detección de fuente parada (el más reciente de todos sus tipos de consulta).
    - `last_item_count` permite reconocer una respuesta vacía donde antes había datos (RF-46).
    """

    __tablename__ = "source_state"

    source: Mapped[str] = mapped_column(closed_values("source", SOURCES), primary_key=True)
    job: Mapped[str] = mapped_column(closed_values("job", SYNC_JOBS), primary_key=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_item_count: Mapped[int | None] = mapped_column(Integer)


class SyncJob(Base):
    """Tarea con fecha: relecturas del historial tras el Champs, reintentos, carga inicial…

    `key` identifica la tarea (p. ej. `history:champs:2026:+24h`) para no programarla dos veces
    (RF-30 a RF-33, RF-3 a RF-5, RF-12, RF-13).
    """

    __tablename__ = "sync_job"
    __table_args__ = (CheckConstraint("attempts >= 0", name="attempts_not_negative"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    kind: Mapped[str] = mapped_column(closed_values("kind", SYNC_JOBS))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"), default=0)
    last_error: Mapped[str | None] = mapped_column(String(MESSAGE_MAX_LENGTH))


class SyncRequest(Base):
    """Petición del administrador: actualizar una fuente o releer el historial (RF-100 a RF-111).

    - `source` es nula en las relecturas del historial.
    - Nunca hay dos peticiones activas (pendiente o en curso) del mismo tipo y fuente: lo
      garantiza un índice único parcial, además de la lógica del proceso (RF-107, RF-108).
    - `result` y `incident_count` se rellenan al terminar (RF-104 a RF-106), también si la
      sesión que la pidió ya ha caducado (RF-136).
    """

    __tablename__ = "sync_request"
    __table_args__ = (
        CheckConstraint("incident_count >= 0", name="incident_count_not_negative"),
        CheckConstraint("(status = 'done') = (result IS NOT NULL)", name="result_when_done"),
        Index(
            "uq_sync_request_active",
            text("kind"),
            text("coalesce(source, '')"),
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    kind: Mapped[str] = mapped_column(closed_values("kind", REQUEST_KINDS))
    source: Mapped[str | None] = mapped_column(closed_values("source", SOURCES))
    status: Mapped[str] = mapped_column(
        closed_values("status", REQUEST_STATUSES), server_default="pending", default="pending"
    )
    result: Mapped[str | None] = mapped_column(closed_values("result", REQUEST_RESULTS))
    incident_count: Mapped[int] = mapped_column(Integer, server_default=text("0"), default=0)
    message: Mapped[str | None] = mapped_column(String(MESSAGE_MAX_LENGTH))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SyncRun(Base):
    """Una consulta a una fuente en el registro de actualizaciones (RF-140, RF-141).

    `message` es texto plano recortado a 500 caracteres (RF-119, RF-120). Se borra a los 7 días.
    """

    __tablename__ = "sync_run"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(closed_values("source", SOURCES))
    job: Mapped[str] = mapped_column(closed_values("job", SYNC_JOBS))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    outcome: Mapped[str] = mapped_column(closed_values("outcome", RUN_OUTCOMES))
    message: Mapped[str | None] = mapped_column(String(MESSAGE_MAX_LENGTH))
    request_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sync_request.id", ondelete="SET NULL"))


class Incident(Base):
    """Incidencia del registro, sin repeticiones (RF-142 a RF-149).

    - Una incidencia idéntica (misma fuente, tipo, dato, valor y motivo) actualiza
      `repetitions` y `last_at` en vez de crear otra fila (RF-147, RF-148). Los campos nulos
      cuentan como iguales para esa comparación.
    - `value_hash` es una huella del valor rechazado, nunca el valor: así el registro no
      guarda datos personales (plan §9).
    - Se borra 7 días después de su última repetición (RF-149).
    """

    __tablename__ = "incident"
    __table_args__ = (
        UniqueConstraint(
            "source", "kind", "subject", "value_hash", "reason",
            name="uq_incident_identity", postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint("repetitions >= 1", name="repetitions_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str | None] = mapped_column(closed_values("source", SOURCES))
    kind: Mapped[str] = mapped_column(closed_values("kind", INCIDENT_KINDS))
    subject: Mapped[str] = mapped_column(String(255))
    value_hash: Mapped[str | None] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(String(MESSAGE_MAX_LENGTH))
    detail: Mapped[str | None] = mapped_column(String(MESSAGE_MAX_LENGTH))
    first_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    repetitions: Mapped[int] = mapped_column(Integer, server_default=text("1"), default=1)


class IncidentDay(Base):
    """Repeticiones de una incidencia en un día natural de Ciudad de México (RF-150 a RF-152)."""

    __tablename__ = "incident_day"
    __table_args__ = (CheckConstraint("repetitions >= 1", name="repetitions_positive"),)

    incident_id: Mapped[int] = mapped_column(ForeignKey("incident.id", ondelete="CASCADE"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    repetitions: Mapped[int] = mapped_column(Integer)


class DailySummary(Base):
    """Resumen de incidencias de un día natural de Ciudad de México (RF-150 a RF-154).

    Solo existe si ese día hubo alguna incidencia (RF-153). Se borra a los 7 días.
    """

    __tablename__ = "daily_summary"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
