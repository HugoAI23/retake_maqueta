"""Frescura de los datos que ve la API (spec 003: RF-89, RF-90, RF-155, RF-158; C-20).

- Un conjunto está sin actualizar si la fuente que lo alimenta lleva más de su umbral sin una
  consulta con éxito (60 s el en vivo, 1 h el resto). Sin ninguna consulta todavía no lo está.
- El en vivo solo puede estarlo mientras haya partidos en vivo, que es cuando se consulta.
- El historial nunca lo está: sus datos solo cambian al importar los archivos de la Wiki (C-20).
- Un partido en vivo está sin actualizar si lleva más de 60 s sin aparecer en ninguna consulta
  con éxito de las fuentes que lo publicaban (RF-90).
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DatasetChange, ExternalRef, Match, SourceState
from app.domain.disappearance import Sighting, is_missing_live
from app.domain.freshness import is_stale
from app.domain.vocabulary import DATASETS

LISTING_JOBS = ("initial_load", "regular")
# Consultas con éxito que incluyen un partido en vivo si sigue publicado (RF-90).
LIVE_JOBS = ("initial_load", "regular", "pre_match", "live")
NEVER_STALE = ("championships",)


def _last_success(session: Session, jobs: tuple[str, ...]) -> dict[str, datetime]:
    """Última consulta con éxito de cada fuente entre los tipos de consulta indicados."""
    latest: dict[str, datetime] = {}
    for state in session.scalars(select(SourceState).where(SourceState.job.in_(jobs),
                                                           SourceState.last_success_at.is_not(None))):
        if state.source not in latest or state.last_success_at > latest[state.source]:
            latest[state.source] = state.last_success_at
    return latest


def freshness(session: Session, now: datetime) -> dict[str, dict]:
    """`lastChangedAt` y `stale` de cada conjunto de datos de la lista cerrada."""
    changed = {row.dataset: row.last_changed_at for row in session.scalars(select(DatasetChange))}
    listing = _last_success(session, LISTING_JOBS).get("bp")
    live_success = _last_success(session, ("live",)).get("bp")
    any_live = session.scalar(select(Match.id).where(Match.status == "live").limit(1)) is not None
    result = {}
    for dataset in DATASETS:
        if dataset in NEVER_STALE:
            stale = False
        elif dataset == "live":
            stale = any_live and is_stale("live", live_success, now)
        else:
            stale = is_stale(dataset, listing, now)
        last_changed = changed.get(dataset)
        result[dataset] = {"last_changed_at": last_changed.astimezone(UTC) if last_changed else None, "stale": stale}
    return result


def match_is_stale(session: Session, match: Match, last_success: dict[str, datetime] | None = None) -> bool:
    """Partido en vivo que lleva más de 60 s sin aparecer en las fuentes que lo publicaban (RF-90)."""
    if match.status != "live":
        return False
    last_success = last_success if last_success is not None else _last_success(session, LIVE_JOBS)
    refs = session.scalars(select(ExternalRef).where(ExternalRef.kind == "match", ExternalRef.entity_id == match.id,
                                                     ExternalRef.last_seen_at.is_not(None)))
    sightings = [Sighting(ref.source, ref.last_seen_at, last_success[ref.source])
                 for ref in refs if ref.source in last_success]
    return is_missing_live(sightings)


def live_last_success(session: Session) -> dict[str, datetime]:
    return _last_success(session, LIVE_JOBS)
