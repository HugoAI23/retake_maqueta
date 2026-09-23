"""T-037 · Historial de campeonatos mundiales."""

from decimal import Decimal

from sqlalchemy import select

from app.db.models import Championship, Identity, Placement, PlacementRoster
from app.ingest.store import entity_for
from tests.integration.ingest.helpers import rec, team


def world(extra=()):
    return [
        *team("F", "[FICTICIO] Viejo", source="wiki", valid_from="2019-01-01T00:00:00Z"),
        rec("identity", "F-id2", source="wiki", franchise_ref="wiki:F", short_name="[FICTICIO] Nuevo",
            valid_from="2026-03-01T00:00:00Z"),
        *[rec("player", f"P{i}", source="wiki", gamertag=f"[FICTICIO] Jugador {i}") for i in range(4)],
        *extra,
    ]


def test_un_premio_por_equipo_aunque_el_roster_tenga_cuatro_jugadores(session, ingest):
    ingest(world([
        rec("championship", "C2026", source="wiki", year=2026, competition="CDL Champs",
            game_name="Call of Duty: Black Ops 6", game_abbreviation="BO6", final_date="2026-06-28", completed=True),
        rec("placement", "P", source="wiki", championship_ref="wiki:C2026", franchise_ref="wiki:F",
            published_team_name="[FICTICIO] Nuevo", place="1", prize_usd=800000, pool_percent=40,
            roster=[{"player_ref": f"wiki:P{i}", "gamertag_at_final": f"[FICTICIO] Entonces {i}"} for i in range(4)]),
    ]))
    placement = session.scalars(select(Placement)).one()
    assert placement.prize_usd == Decimal("800000")
    assert placement.pool_percent == Decimal("40")
    rosters = session.scalars(select(PlacementRoster)).all()
    assert len(rosters) == 4
    assert {r.gamertag_at_final for r in rosters} == {f"[FICTICIO] Entonces {i}" for i in range(4)}
    championship = session.scalars(select(Championship)).one()
    assert (championship.game_abbreviation, championship.completed) == ("BO6", True)


def identity_name(session, placement):
    return session.get(Identity, placement.identity_id).short_name


def test_lugar_dq_y_rango_se_guardan_tal_cual(session, ingest):
    ingest(world([
        rec("championship", "C2019", source="wiki", year=2019, completed=True),
        *team("G", "[FICTICIO] Otro", source="wiki", valid_from="2018-01-01T00:00:00Z"),
        rec("placement", "P1", source="wiki", championship_ref="wiki:C2019", franchise_ref="wiki:F", place="DQ"),
        rec("placement", "P2", source="wiki", championship_ref="wiki:C2019", franchise_ref="wiki:G", place="9-12"),
    ]))
    rows = {p.place: p.is_dq for p in session.scalars(select(Placement))}
    assert rows == {"DQ": True, "9-12": False}


def test_identidad_de_la_final_con_fecha_por_nombre_o_a_fin_de_anio(session, ingest):
    ingest(world([
        rec("championship", "C2026", source="wiki", year=2026, final_date="2026-02-15", completed=True),
        rec("championship", "C2025", source="wiki", year=2025, completed=True),
        rec("championship", "C2027", source="wiki", year=2027, completed=True),
        rec("placement", "A", source="wiki", championship_ref="wiki:C2026", franchise_ref="wiki:F", place="1"),
        rec("placement", "B", source="wiki", championship_ref="wiki:C2025", franchise_ref="wiki:F", place="1",
            published_team_name="[FICTICIO] nuevo"),
        rec("placement", "C", source="wiki", championship_ref="wiki:C2027", franchise_ref="wiki:F", place="1",
            published_team_name="Nombre desconocido"),
    ]))
    by_year = {session.get(Championship, p.championship_id).year: p for p in session.scalars(select(Placement))}
    assert identity_name(session, by_year[2026]) == "[FICTICIO] Viejo"  # final antes del cambio de marzo
    assert identity_name(session, by_year[2025]) == "[FICTICIO] Nuevo"  # coincide por nombre
    assert identity_name(session, by_year[2027]) == "[FICTICIO] Nuevo"  # vigente el 31-12-2027


def test_campeonato_incompleto_se_registra_con_lo_que_haya(session, ingest):
    ingest(world([
        rec("championship", "C2014", source="wiki", year=2014, completed=True),
        rec("placement", "P", source="wiki", championship_ref="wiki:C2014", franchise_ref="wiki:F",
            roster=[{"player_ref": "wiki:P0"}]),
    ]))
    placement = session.scalars(select(Placement)).one()
    assert (placement.place, placement.prize_usd, placement.pool_percent) == (None, None, None)
    assert session.scalars(select(PlacementRoster)).one().gamertag_at_final is None


def test_una_correccion_en_el_historial_se_marca(session, ingest):
    ingest(world([
        rec("championship", "C2020", source="wiki", year=2020, completed=True),
        rec("placement", "P", source="wiki", championship_ref="wiki:C2020", franchise_ref="wiki:F", place="1", prize_usd=100),
    ]))
    ingest([rec("placement", "P", source="wiki", hours=1, championship_ref="wiki:C2020", franchise_ref="wiki:F",
                place="1", prize_usd=120)])
    session.expire_all()
    placement = session.scalars(select(Placement)).one()
    assert placement.prize_usd == Decimal("120")
    assert placement.corrected_fields == ["prize_usd"]
    assert entity_for(session, "championship", "wiki:C2020") == placement.championship_id
