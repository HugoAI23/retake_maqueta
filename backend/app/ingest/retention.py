"""Registros retenidos (spec 003: RF-54 a RF-56 con la nota C-14; T-043).

Una referencia de partido, evento, franquicia o jugador queda retenida si no está enlazada con
ninguna de otra fuente, una fuente de más prioridad publica referencias de ese tipo y la
curación no la ha confirmado como nueva. Se recalcula en cada ingesta: la fuente principal
puede empezar a publicar un tipo después, y una unión o una confirmación la liberan (RF-56).
"""

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Event, ExternalRef, Franchise, Match, Player
from app.domain.priority import SOURCE_PRIORITY
from app.ingest.changes import touch

RETAINABLE = {"match": Match, "event": Event, "franchise": Franchise, "player": Player}


def update_retention(session: Session, now: datetime, confirmed: set[tuple[str, str, str]] = frozenset()) -> list[str]:
    """Fija o retira `retained_since` y devuelve las referencias recién retenidas (`fuente:id`).

    Args:
        confirmed: Referencias confirmadas como nuevas por la curación, como `(tipo, fuente, id)`.
    """
    session.flush()
    newly: list[str] = []
    for kind, model in RETAINABLE.items():
        refs = session.scalars(select(ExternalRef).where(ExternalRef.kind == kind).order_by(ExternalRef.id)).all()
        present = {ref.source for ref in refs}
        sources_of: dict = defaultdict(set)
        for ref in refs:
            sources_of[ref.entity_id].add(ref.source)
        for ref in refs:
            higher = SOURCE_PRIORITY[:SOURCE_PRIORITY.index(ref.source)] if ref.source in SOURCE_PRIORITY else ()
            retain = (
                any(source in present for source in higher)
                and sources_of[ref.entity_id] == {ref.source}
                and (kind, ref.source, ref.source_id) not in confirmed
            )
            if retain == (ref.retained_since is not None):
                continue
            ref.retained_since = now if retain else None
            if retain:
                newly.append(f"{ref.source}:{ref.source_id}")
            entity = session.get(model, ref.entity_id) if ref.entity_id else None
            if entity is not None:
                touch(session, entity)  # cambia lo que se muestra de la temporada actual
    session.flush()
    return newly
