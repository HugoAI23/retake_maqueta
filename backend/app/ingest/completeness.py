"""Cuándo un partido finalizado tiene todas sus estadísticas (spec 003: RF-19, RF-20; T-046).

Criterio de RF-47 de la 002: faltan estadísticas si a algún mapa jugado le faltan todas las de
algún jugador; un mapa jugado sin ninguna estadística también las tiene pendientes. Una
estadística suelta ausente no cuenta (RF-72 de la 002). Un partido sin mapas jugados, como un
forfeit, las tiene todas desde que finaliza.
"""

from collections import defaultdict
from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.db.models import Match, MatchMap, PlayerMapStats
from app.ingest.resolvers import COMMON_STATS, MODE_STATS

STAT_COLUMNS = tuple(dict.fromkeys(COMMON_STATS + sum(MODE_STATS.values(), ())))


def _has_any_stat(stats: PlayerMapStats) -> bool:
    return any(getattr(stats, column) is not None for column in STAT_COLUMNS)


def update_stats_complete(session: Session, now: datetime) -> None:
    """Fija `stats_complete_at` al completarse, lo retira si vuelven a faltar y lo vacía si no está finalizado.

    La marca no se mueve mientras sigan completas: de ella cuenta la revisión de 7 días (RF-20).
    """
    session.flush()
    session.execute(update(Match).where(Match.status != "finished", Match.stats_complete_at.is_not(None))
                    .values(stats_complete_at=None).execution_options(synchronize_session="fetch"))

    pending: set = set()
    maps_by_id = {m.id: m.match_id for m in session.scalars(
        select(MatchMap).join(Match, Match.id == MatchMap.match_id)
        .where(Match.status == "finished", MatchMap.played.is_(True)))}
    stats_by_map: dict = defaultdict(list)
    for stats in session.scalars(select(PlayerMapStats).where(PlayerMapStats.map_id.in_(maps_by_id))):
        stats_by_map[stats.map_id].append(stats)
    for map_id, match_id in maps_by_id.items():
        rows = stats_by_map.get(map_id, [])
        if not rows or not all(_has_any_stat(row) for row in rows):
            pending.add(match_id)

    for match in session.scalars(select(Match).where(Match.status == "finished", or_(
            Match.stats_complete_at.is_(None), Match.id.in_(pending)))):
        if match.id in pending:
            match.stats_complete_at = None
        elif match.stats_complete_at is None:
            match.stats_complete_at = now
    session.flush()
