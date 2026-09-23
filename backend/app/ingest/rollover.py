"""Cambio de temporada (RF-1, RF-80, RF-105, RF-116; plan §3.5).

Cuando una temporada nueva empieza, se borra el detalle competitivo de las anteriores
y lo que ya no figura ni en la temporada nueva ni en el historial de campeonatos.
El historial no se toca: viene de sus propios registros (RF-4, RF-55).
"""

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.db.models import (
    Event,
    ExternalRef,
    Franchise,
    MatchSlot,
    Placement,
    PlacementRoster,
    Player,
    PlayerMapStats,
    RosterMembership,
    Season,
    Standing,
)
from app.ingest.store import KIND_MODELS


def delete_orphan_refs(session: Session) -> None:
    """Borra las referencias externas (y sus observaciones) cuya entidad ya no existe."""
    for kind, model in KIND_MODELS.items():
        alive = exists().where(model.id == ExternalRef.entity_id)
        session.execute(
            delete(ExternalRef).where(ExternalRef.kind == kind, ExternalRef.entity_id.is_not(None), ~alive)
        )


def roll_over(session: Session, new_year: int) -> None:
    """Aplica el cambio a la temporada `new_year`, que acaba de empezar."""
    old_seasons = select(Season.id).where(Season.year < new_year)
    # Los partidos, mapas, horarios, lados y estadísticas se borran en cascada con sus eventos.
    session.execute(delete(Event).where(Event.season_id.in_(old_seasons)))
    session.execute(delete(Standing).where(Standing.season_id.in_(old_seasons)))
    session.execute(delete(RosterMembership).where(RosterMembership.season_id.in_(old_seasons)))

    # Jugadores que ya no figuran en ninguna parte (RF-80, RF-105).
    session.execute(delete(Player).where(
        ~exists().where(RosterMembership.player_id == Player.id),
        ~exists().where(PlayerMapStats.player_id == Player.id),
        ~exists().where(PlacementRoster.player_id == Player.id),
    ))
    # Franquicias que dejan la liga y no figuran en el historial (RF-116).
    session.execute(delete(Franchise).where(
        ~exists().where(RosterMembership.franchise_id == Franchise.id),
        ~exists().where(MatchSlot.franchise_id == Franchise.id),
        ~exists().where(PlayerMapStats.franchise_id == Franchise.id),
        ~exists().where(Standing.franchise_id == Franchise.id),
        ~exists().where(Placement.franchise_id == Franchise.id),
    ))
    delete_orphan_refs(session)
    session.flush()
    session.expire_all()
