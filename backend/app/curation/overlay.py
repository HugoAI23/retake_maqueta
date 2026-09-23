"""Aplicación de la curación encima de los datos de las fuentes (plan §2.2, P-4, D-17).

Se aplica entera o no se aplica: si algo falla, se lanza `CurationError` y quien llama
deshace la transacción. Aplicarla dos veces da el mismo resultado.
"""

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.curation.loader import Curation, CurationError
from app.db.models import Observation, Player
from app.domain.entity_links import CurationConflictError
from app.ingest.pipeline import apply_regroup
from app.ingest.resolvers import PERSONAL_FIELDS, IngestContext, delete_orphan_rows, reresolve_entity
from app.ingest.store import find_ref, refs_of_entity


def _referenced_keys(curation: Curation):
    for entry in curation.roles:
        yield entry.player
    for entry in curation.player_merges:
        yield from entry.players
    for entry in curation.player_splits:
        yield from entry.players
    for entry in curation.personal_data_removals:
        yield entry.player


def apply_curation(session: Session, curation: Curation) -> None:
    """Aplica roles, uniones, separaciones y retiradas de datos personales.

    Raises:
        CurationError: si una referencia no existe o la curación se contradice.
    """
    unknown = sorted({str(key) for key in _referenced_keys(curation) if find_ref(session, "player", key) is None})
    if unknown:
        raise CurationError("Referencias desconocidas en la curación: " + ", ".join(unknown))

    ctx = IngestContext(session=session, curation=curation, detect_corrections=False)
    try:
        apply_regroup(ctx, "player")
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
    session.flush()
