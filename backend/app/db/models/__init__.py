"""Modelos de la base de datos (plan de la spec 002, §3, y plan de la spec 003, §4).

Importar este paquete registra todas las tablas en `Base.metadata`, que es lo que
lee Alembic para generar las migraciones.
"""

from app.db.models.admin import AdminSession, AdminUser, LoginOrigin
from app.db.models.history import Championship, Placement, PlacementRoster, Standing
from app.db.models.inputs import ExternalRef, Observation, RefLink
from app.db.models.league import Event, Franchise, Identity, Season
from app.db.models.logos import LogoImage
from app.db.models.matches import (
    PLAYER_STAT_FIELDS,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    PlayerMapStats,
)
from app.db.models.players import Player, PlayerGamertag, RosterMembership
from app.db.models.sync import (
    DailySummary,
    DatasetChange,
    Incident,
    IncidentDay,
    SourceState,
    SyncJob,
    SyncRequest,
    SyncRun,
)

__all__ = [
    "PLAYER_STAT_FIELDS",
    "AdminSession",
    "AdminUser",
    "Championship",
    "DailySummary",
    "DatasetChange",
    "Event",
    "ExternalRef",
    "Franchise",
    "Identity",
    "Incident",
    "IncidentDay",
    "LoginOrigin",
    "LogoImage",
    "Match",
    "MatchMap",
    "MatchSchedule",
    "MatchSlot",
    "Observation",
    "Placement",
    "PlacementRoster",
    "Player",
    "PlayerGamertag",
    "PlayerMapStats",
    "RefLink",
    "RosterMembership",
    "Season",
    "SourceState",
    "Standing",
    "SyncJob",
    "SyncRequest",
    "SyncRun",
]
