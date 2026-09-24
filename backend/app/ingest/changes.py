"""Hora del último cambio de cada fila y de cada conjunto de datos (spec 003: RF-155 a RF-159; plan D-7).

Durante una ingesta, justo antes de cada escritura en la base de datos, se miran las filas
nuevas, modificadas o borradas de las tablas resueltas:

- una fila nueva o cuyo valor cambia de verdad recibe `changed_at` = hora de la ingesta
  (reasignar el mismo valor no cuenta: SQLAlchemy solo la marca si el valor es distinto);
- los cambios de horarios, lados, gamertags anteriores y rosters de campeonato mueven la
  hora de su fila madre (partido, jugador o clasificación);
- se anota qué conjuntos de datos cambiaron, para `dataset_change` y el aviso a la API.
"""

from datetime import datetime

from sqlalchemy import event, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import (
    Championship,
    DatasetChange,
    Event,
    Identity,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    Placement,
    PlacementRoster,
    Player,
    PlayerGamertag,
    PlayerMapStats,
    RosterMembership,
    Season,
    Standing,
)

# Tabla resuelta → conjunto de datos que cambia (lista cerrada DATASETS).
DATASET_OF = {
    Season: "season",
    Event: "events",
    Identity: "franchises",
    Player: "players",
    RosterMembership: "players",
    Match: "matches",
    MatchMap: "matches",
    PlayerMapStats: "matches",
    Standing: "standings",
    Championship: "championships",
    Placement: "championships",
}

# Filas hijas sin `changed_at`: su cambio mueve la hora de la fila madre.
PARENT_OF = {
    MatchSchedule: (Match, "match_id"),
    MatchSlot: (Match, "match_id"),
    PlayerGamertag: (Player, "player_id"),
    PlacementRoster: (Placement, "placement_id"),
}


# Clave de `session.info` con el rastreador enganchado a la sesión.
TRACKER = "retake_change_tracker"

# Conjuntos que cambian con un cambio de temporada: se borra el detalle de la anterior (RF-1 de la 002).
ROLLOVER_DATASETS = {"season", "events", "matches", "live", "standings", "players", "franchises"}


def touch(session: Session, obj) -> None:
    """Marca como cambiada una fila cuyo cambio no pasa por sus atributos (p. ej. borrar sus hijas).

    Se marca en el acto: si no hay nada más pendiente de escribir, SQLAlchemy no lanza el aviso
    previo a la escritura y el enganche no la vería.
    """
    tracker = session.info.get(TRACKER)
    if tracker is not None:
        tracker._mark(session, obj)


class ChangeTracker:
    """Marca los cambios de una sesión mientras está enganchado a ella."""

    def __init__(self, now: datetime):
        self.now = now
        self.changed: set[str] = set()
        self._session: Session | None = None

    def _mark(self, session: Session, obj, deleted: bool = False) -> None:
        model = type(obj)
        if model in PARENT_OF:
            parent_model, column = PARENT_OF[model]
            parent = session.get(parent_model, getattr(obj, column)) if getattr(obj, column) else None
            if parent is not None and parent not in session.deleted:
                self._mark(session, parent)
            return
        if model not in DATASET_OF:
            return
        self.changed.add(DATASET_OF[model])
        if model is Match and getattr(obj, "status", None) == "live":
            self.changed.add("live")
        if not deleted:
            obj.changed_at = self.now

    def _before_flush(self, session: Session, flush_context, instances) -> None:
        for obj in list(session.new):
            self._mark(session, obj)
        for obj in list(session.dirty):
            if session.is_modified(obj, include_collections=False):
                self._mark(session, obj)
        for obj in list(session.deleted):
            self._mark(session, obj, deleted=True)

    def rolled_over(self) -> None:
        """Un cambio de temporada borra en bloque el detalle de la anterior."""
        self.changed |= ROLLOVER_DATASETS

    def attach(self, session: Session) -> None:
        self._session = session
        session.info[TRACKER] = self
        event.listen(session, "before_flush", self._before_flush)

    def detach(self) -> None:
        if self._session is not None:
            self._session.info.pop(TRACKER, None)
            event.remove(self._session, "before_flush", self._before_flush)
            self._session = None

    def save(self, session: Session) -> None:
        """Guarda en `dataset_change` la hora de los conjuntos que cambiaron (RF-158)."""
        for dataset in sorted(self.changed):
            session.execute(
                insert(DatasetChange).values(dataset=dataset, last_changed_at=self.now)
                .on_conflict_do_update(index_elements=["dataset"], set_={"last_changed_at": self.now})
            )
        session.flush()


def last_changed(session: Session) -> dict[str, datetime]:
    """Último cambio de cada conjunto de datos."""
    return dict(session.execute(select(DatasetChange.dataset, DatasetChange.last_changed_at)).all())
