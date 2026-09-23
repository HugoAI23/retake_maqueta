"""T-040 · Cambio de temporada (RF-1, RF-80, RF-105, RF-116)."""

from sqlalchemy import func, select

from app.db.models import Event, ExternalRef, Franchise, Match, Player, RosterMembership, Standing
from app.db.queries import current_season
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec, season_and_event, team


def test_al_empezar_la_temporada_nueva_se_borra_el_detalle_de_la_anterior(session, ingest):
    ingest([
        *season_and_event(2026, "ev2026"),
        *team("t1", "[FICTICIO] Solo 2026"),
        *team("t2", "[FICTICIO] Campeón histórico"),
        rec("player", "a", gamertag="[FICTICIO] Solo 2026"),
        rec("player", "b", gamertag="[FICTICIO] Histórico"),
        rec("roster", "ra", season_year=2026, franchise_ref="bp:t1", player_ref="bp:a"),
        rec("match", "m2026", event_ref="bp:ev2026", best_of=5, status="live", slots=[{"franchise_ref": "bp:t1"}, None]),
        rec("standing", "st", season_year=2026, franchise_ref="bp:t1", position=1, points=10),
        rec("championship", "c2025", year=2025, completed=True),
        rec("placement", "p", championship_ref="bp:c2025", franchise_ref="bp:t2", place="1", roster=[{"player_ref": "bp:b"}]),
    ])
    assert current_season(session).year == 2026
    kept_player = entity_for(session, "player", "bp:b")

    ingest([*season_and_event(2027, "ev2027"),
            rec("match", "m2027", hours=1, event_ref="bp:ev2027", best_of=5, status="live")])
    session.expire_all()

    assert current_season(session).year == 2027
    assert [e.name for e in session.scalars(select(Event))] == ["[FICTICIO] Major 2027"]
    assert session.scalar(select(func.count()).select_from(Match)) == 1
    assert session.scalars(select(Standing)).all() == []
    assert session.scalars(select(RosterMembership)).all() == []
    assert [p.id for p in session.scalars(select(Player))] == [kept_player]
    assert [f.id for f in session.scalars(select(Franchise))] == [entity_for(session, "franchise", "bp:t2")]
    # Las referencias de lo borrado también desaparecen.
    assert session.scalar(select(func.count()).select_from(ExternalRef).where(ExternalRef.source_id == "a")) == 0
    assert entity_for(session, "player", "bp:b") == kept_player
