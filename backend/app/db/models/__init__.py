"""Modelos de la base de datos (plan de la spec 002, §3).

Importar este paquete registra todas las tablas en `Base.metadata`, que es lo que
lee Alembic para generar las migraciones.
"""

from app.db.models.history import Championship, Placement, PlacementRoster, Standing
from app.db.models.inputs import ExternalRef, Observation, RefLink
from app.db.models.league import Event, Franchise, Identity, Season
from app.db.models.matches import (
    PLAYER_STAT_FIELDS,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    PlayerMapStats,
)
from app.db.models.players import Player, PlayerGamertag, RosterMembership

__all__ = [
    "PLAYER_STAT_FIELDS",
    "Championship",
    "Event",
    "ExternalRef",
    "Franchise",
    "Identity",
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
    "Standing",
]
