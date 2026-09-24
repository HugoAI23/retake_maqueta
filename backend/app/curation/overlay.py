"""Aplicación de la curación encima de los datos de las fuentes (plan §2.2, P-4, D-17).

Se aplica entera o no se aplica: si algo falla, se lanza `CurationError` y quien llama
deshace la transacción. Aplicarla dos veces da el mismo resultado.
"""

from datetime import UTC, datetime

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.curation.loader import Curation, CurationError
from app.db.models import Observation, Player
from app.domain.entity_links import CurationConflictError
from app.ingest.pipeline import apply_regroup, confirmed_keys
from app.ingest.resolvers import PERSONAL_FIELDS, IngestContext, delete_orphan_rows, reresolve_entity
from app.ingest.retention import update_retention
from app.ingest.store import find_ref, refs_of_entity


def _referenced_keys(curation: Curation):
    """Referencias que nombra la curación, como `(tipo, referencia)`."""
    for entry in curation.roles:
        yield "player", entry.player
    for entry in curation.player_merges:
        yield from (("player", key) for key in entry.players)
    for entry in curation.player_splits:
        yield from (("player", key) for key in entry.players)
    for entry in curation.personal_data_removals:
        yield "player", entry.player
    for entry in curation.merges:
        yield from ((entry.kind, key) for key in entry.refs)
    for entry in curation.confirmed_new:
        yield entry.kind, entry.ref


def apply_curation(session: Session, curation: Curation, now: datetime | None = None) -> None:
    """Aplica roles, uniones, separaciones y retiradas de datos personales.

    Raises:
        CurationError: si una referencia no existe o la curación se contradice.
    """
    unknown = sorted({f"{key.source}:{key.source_id}" for kind, key in _referenced_keys(curation)
                      if find_ref(session, kind, key) is None})
    if unknown:
        raise CurationError("Referencias desconocidas en la curación: " + ", ".join(unknown))

    ctx = IngestContext(session=session, curation=curation, detect_corrections=False)
    try:
        # Spec 003 (T-044): primero franquicias y eventos, de los que cuelgan partidos y jugadores.
        for kind in ("franchise", "event", "match", "player"):
            apply_regroup(ctx, kind)
    except CurationConflictError as error:
        raise CurationError(str(error)) from None

    # Roles (RF-26, RF-27, RF-76): el archivo es la única fuente; sin entrada, sin rol.
    session.execute(update(Player).values(role=None))
    for entry in curation.roles:
        player = session.get(Player, find_ref(session, "player", entry.player).entity_id)
        player.role = entry.role

    # Retiradas de datos personales (RF-78): se borran y no se vuelven a guardar.
    for entry in curation.personal_data_removals:
        player = session.get(Player, find_ref(session, "player", entry.player).entity_id)
        player.personal_data_removed = True
        ref_ids = [ref.id for ref in refs_of_entity(session, "player", player.id)]
        session.execute(delete(Observation).where(
            Observation.ref_id.in_(ref_ids), Observation.field.in_(PERSONAL_FIELDS)))
        session.flush()
        reresolve_entity(ctx, "player", player.id)

    delete_orphan_rows(session)
    # Spec 003 (RF-56): unir o confirmar como nuevo libera los registros retenidos.
    update_retention(session, now or datetime.now(UTC), confirmed_keys(curation))
    session.flush()
