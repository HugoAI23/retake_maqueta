"""Prueba del esquema inicial (T-016): una fila en cada tabla y restricciones clave."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import (
    Championship,
    Event,
    ExternalRef,
    Franchise,
    Identity,
    Match,
    MatchMap,
    MatchSchedule,
    MatchSlot,
    Observation,
    Placement,
    PlacementRoster,
    Player,
    PlayerGamertag,
    PlayerMapStats,
    RefLink,
    RosterMembership,
    Season,
    Standing,
)

NOW = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


def test_la_migracion_crea_todas_las_tablas_de_los_modelos(clean_db):
    tables = set(inspect(clean_db).get_table_names()) - {"alembic_version"}
    assert tables == set(Base.metadata.tables)


def test_una_fila_en_cada_tabla(clean_db):
    with Session(clean_db) as session:
        season = Season(year=2026, name="CDL 2026", started_at=NOW)
        franchise = Franchise()
        session.add_all([season, franchise])
        session.flush()

        ref = ExternalRef(kind="player", source="bp", source_id="123")
        other_ref = ExternalRef(kind="player", source="wiki", source_id="Player_X")
        session.add_all([ref, other_ref])
        session.flush()
        session.add(RefLink(from_ref_id=ref.id, to_ref_id=other_ref.id, link_type="same_as"))
        session.add(Observation(ref_id=ref.id, field="kills", value=25, is_valid=True,
                                first_seen_at=NOW, last_seen_at=NOW))

        identity = Identity(franchise_id=franchise.id, short_name="[FICTICIO] Equipo A",
                            abbreviation="FTA", valid_from=NOW)
        event = Event(season_id=season.id, name="[FICTICIO] Major 1")
        player = Player(current_gamertag="[FICTICIO] Jugador", birth_year=2002, role="SMG")
        session.add_all([identity, event, player])
        session.flush()

        session.add(PlayerGamertag(player_id=player.id, gamertag="[FICTICIO] Antiguo", position=1))
        session.add(RosterMembership(season_id=season.id, player_id=player.id, franchise_id=franchise.id))

        match = Match(event_id=event.id, phase="grand_final", best_of=5, status="finished",
                      maps_won_1=3, maps_won_2=1, winner_side=1)
        session.add(match)
        session.flush()
        session.add(MatchSchedule(match_id=match.id, scheduled_at=NOW, seq=1))
        session.add(MatchSlot(match_id=match.id, side=1, franchise_id=franchise.id))
        game_map = MatchMap(match_id=match.id, position=1, mode="Hardpoint", map_name="Vault",
                            played=True, score_1=250, score_2=200, winner_side=1)
        session.add(game_map)
        session.flush()
        session.add(PlayerMapStats(map_id=game_map.id, player_id=player.id, franchise_id=franchise.id,
                                   kills=25, deaths=20, kd=Decimal("1.25"), hill_time=90))

        session.add(Standing(season_id=season.id, franchise_id=franchise.id, position=1, points=240))
        championship = Championship(year=2026, competition="CDL Champs", game_name="Call of Duty: Black Ops 6",
                                    game_abbreviation="BO6", final_date=date(2026, 6, 28), completed=True)
        session.add(championship)
        session.flush()
        placement = Placement(championship_id=championship.id, franchise_id=franchise.id,
                              identity_id=identity.id, place="1", prize_usd=Decimal("800000.00"),
                              pool_percent=Decimal("40.000"))
        session.add(placement)
        session.flush()
        session.add(PlacementRoster(placement_id=placement.id, player_id=player.id,
                                    gamertag_at_final="[FICTICIO] Antiguo"))
        session.commit()

    with Session(clean_db) as session:
        for model in Base.metadata.tables:
            count = session.connection().exec_driver_sql(f'SELECT count(*) FROM "{model}"').scalar_one()
            assert count >= 1, f"la tabla {model} está vacía"
        stored = session.query(PlayerMapStats).one()
        assert stored.kd == Decimal("1.250")
        assert stored.corrected_fields == []
        assert session.query(Match).one().corrected_fields == []


def test_el_anio_de_temporada_es_unico(clean_db):
    with Session(clean_db) as session:
        session.add_all([Season(year=2026), Season(year=2026)])
        with pytest.raises(IntegrityError):
            session.flush()


def _new_match(session: Session, **fields) -> Match:
    season = Season(year=2026)
    session.add(season)
    session.flush()
    event = Event(season_id=season.id, name="[FICTICIO] Evento")
    session.add(event)
    session.flush()
    match = Match(event_id=event.id, best_of=5, **fields)
    session.add(match)
    return match


def test_una_fase_fuera_de_la_lista_se_rechaza(clean_db):
    with Session(clean_db) as session:
        _new_match(session, phase="final")
        with pytest.raises(IntegrityError):
            session.flush()


def test_un_partido_sin_fase_se_acepta(clean_db):
    with Session(clean_db) as session:
        _new_match(session, phase=None)
        session.flush()


def _stats(session: Session, **stats) -> PlayerMapStats:
    match = _new_match(session)
    player = Player(current_gamertag="[FICTICIO] Jugador")
    session.add(player)
    session.flush()
    game_map = MatchMap(match_id=match.id, position=1, played=True)
    session.add(game_map)
    session.flush()
    row = PlayerMapStats(map_id=game_map.id, player_id=player.id, **stats)
    session.add(row)
    return row


def test_una_estadistica_nula_se_acepta_y_sigue_siendo_nula(clean_db):
    with Session(clean_db) as session:
        row = _stats(session, kills=0, deaths=None)
        session.commit()
        session.refresh(row)
        assert row.kills == 0
        assert row.deaths is None


def test_una_estadistica_negativa_se_rechaza_aunque_otras_sean_nulas(clean_db):
    with Session(clean_db) as session:
        _stats(session, kills=None, deaths=-1)
        with pytest.raises(IntegrityError):
            session.flush()


def test_un_porcentaje_de_bolsa_mayor_que_100_se_rechaza(clean_db):
    with Session(clean_db) as session:
        championship = Championship(year=2020)
        franchise = Franchise()
        session.add_all([championship, franchise])
        session.flush()
        session.add(Placement(championship_id=championship.id, franchise_id=franchise.id,
                              pool_percent=Decimal("100.5")))
        with pytest.raises(IntegrityError):
            session.flush()
