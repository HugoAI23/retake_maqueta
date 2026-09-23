"""Pruebas del esquema de la spec 003 (T-010 a T-014).

- La migración se aplica sobre una base de datos con los datos de prueba de la 002 sin perder nada.
- Las migraciones de la 003 se aplican y se deshacen sin errores.
- Las columnas y tablas nuevas existen y sus restricciones rechazan valores fuera de las listas cerradas.
- Solo puede existir una cuenta de administrador (RF-121).
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    AdminSession,
    AdminUser,
    DailySummary,
    DatasetChange,
    Event,
    ExternalRef,
    Franchise,
    Identity,
    Incident,
    IncidentDay,
    LoginOrigin,
    LogoImage,
    Match,
    MatchMap,
    Observation,
    Placement,
    Player,
    PlayerMapStats,
    Season,
    SourceState,
    Standing,
    SyncJob,
    SyncRequest,
    SyncRun,
)
from tests.conftest import BACKEND_DIR

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
LAST_002_REVISION = "737618706e21"


def _alembic(test_database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = test_database_url
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture
def db_at_002(test_engine, test_database_url):
    """`retake_test` vacía con el esquema de la spec 002 (sin las migraciones de la 003)."""
    with test_engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    command.upgrade(_alembic(test_database_url), LAST_002_REVISION)
    return test_engine


COUNTED_TABLES = (
    "external_ref", "observation", "ref_link", "season", "event", "franchise", "identity", "player",
    "player_gamertag", "roster_membership", "match", "match_schedule", "match_slot", "match_map",
    "player_map_stats", "standing", "championship", "placement", "placement_roster",
)


def _counts(engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {t: connection.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in COUNTED_TABLES}


# --- T-010: la migración conserva los datos de la 002 --------------------------------------


def test_la_migracion_conserva_los_datos_de_prueba_de_la_002(db_at_002, test_database_url):
    # Los datos de prueba se cargan con los modelos de la 002 (a mano, con SQL), porque los
    # modelos de Python ya tienen las columnas nuevas y el esquema todavía no.
    with db_at_002.begin() as connection:
        season_id, event_id, franchise_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        match_id, player_id = uuid.uuid4(), uuid.uuid4()
        connection.execute(text("INSERT INTO season (id, year, name, started_at) VALUES (:i, 2026, 'CDL 2026', :t)"),
                           {"i": season_id, "t": NOW})
        connection.execute(text("INSERT INTO event (id, season_id, name) VALUES (:i, :s, '[FICTICIO] Major 1')"),
                           {"i": event_id, "s": season_id})
        connection.execute(text("INSERT INTO franchise (id) VALUES (:i)"), {"i": franchise_id})
        connection.execute(text(
            "INSERT INTO identity (id, franchise_id, short_name, valid_from) VALUES (:i, :f, '[FICTICIO] A', :t)"),
            {"i": uuid.uuid4(), "f": franchise_id, "t": NOW})
        connection.execute(text("INSERT INTO player (id, current_gamertag) VALUES (:i, '[FICTICIO] J')"),
                           {"i": player_id})
        connection.execute(text(
            "INSERT INTO match (id, event_id, best_of, status) VALUES (:i, :e, 5, 'finished')"),
            {"i": match_id, "e": event_id})
        connection.execute(text(
            "INSERT INTO external_ref (kind, source, source_id) VALUES ('match', 'bp', '1')"))
        connection.execute(text(
            "INSERT INTO observation (ref_id, field, value, is_valid, first_seen_at, last_seen_at) "
            "SELECT id, 'kills', '-3', false, :t, :t FROM external_ref"), {"t": NOW})
    before = _counts(db_at_002)

    command.upgrade(_alembic(test_database_url), "head")

    assert _counts(db_at_002) == before
    with Session(db_at_002) as session:
        # Las columnas nuevas llegan vacías: nada se inventa sobre los datos que ya había.
        observation = session.scalars(select(Observation)).one()
        assert observation.invalid_reason is None
        assert session.scalars(select(ExternalRef)).one().last_seen_at is None
        match = session.scalars(select(Match)).one()
        assert (match.changed_at, match.stats_complete_at, match.disappeared_at) == (None, None, None)


# --- T-010 a T-013: las migraciones se aplican y se deshacen ---------------------------------


def test_las_migraciones_de_la_003_se_aplican_y_se_deshacen(clean_db, test_database_url):
    config = _alembic(test_database_url)
    command.downgrade(config, LAST_002_REVISION)
    tables = set(inspect(clean_db).get_table_names())
    assert not tables & {"logo_image", "sync_run", "incident", "admin_user"}
    assert "last_seen_at" not in {c["name"] for c in inspect(clean_db).get_columns("external_ref")}
    command.upgrade(config, "head")
    assert {"logo_image", "sync_run", "incident", "admin_user"} <= set(inspect(clean_db).get_table_names())


# --- T-014: columnas nuevas --------------------------------------------------------------------


@pytest.mark.parametrize("table", [
    "season", "event", "identity", "player", "roster_membership", "match", "match_map",
    "player_map_stats", "standing", "championship", "placement",
])
def test_las_tablas_resueltas_tienen_changed_at(clean_db, table):
    assert "changed_at" in {c["name"] for c in inspect(clean_db).get_columns(table)}


def test_columnas_nuevas_de_referencias_observaciones_partidos_e_identidades(clean_db):
    columns = lambda table: {c["name"] for c in inspect(clean_db).get_columns(table)}  # noqa: E731
    assert {"last_seen_at", "retained_since"} <= columns("external_ref")
    assert "invalid_reason" in columns("observation")
    assert {"stats_complete_at", "disappeared_at"} <= columns("match")
    assert "logo_image_id" in columns("identity")


# --- T-014: restricciones de las listas cerradas -----------------------------------------------


def _rejects(engine, *objects) -> None:
    with Session(engine) as session:
        session.add_all(objects)
        with pytest.raises(IntegrityError):
            session.flush()


def test_la_razon_de_invalidez_solo_admite_imposible_o_ilegible(clean_db):
    with Session(clean_db) as session:
        ref = ExternalRef(kind="match", source="bp", source_id="1")
        session.add(ref)
        session.flush()
        for reason in ("impossible", "unreadable"):
            session.add(Observation(ref_id=ref.id, field=f"f_{reason}", value=None, is_valid=False,
                                    invalid_reason=reason, first_seen_at=NOW, last_seen_at=NOW))
        session.flush()
        session.add(Observation(ref_id=ref.id, field="otro", value=None, is_valid=False,
                                invalid_reason="unknown", first_seen_at=NOW, last_seen_at=NOW))
        with pytest.raises(IntegrityError):
            session.flush()


def test_logo_solo_png_jpeg_o_webp_y_hasta_un_mega(clean_db):
    ok = LogoImage(id="a" * 64, content=b"x", media_type="image/png", size_bytes=1, width=1, height=1,
                   first_seen_at=NOW)
    with Session(clean_db) as session:
        session.add(ok)
        session.commit()
    _rejects(clean_db, LogoImage(id="b" * 64, content=b"x", media_type="image/svg+xml", size_bytes=1,
                                 width=1, height=1, first_seen_at=NOW))
    _rejects(clean_db, LogoImage(id="c" * 64, content=b"x", media_type="image/png", size_bytes=1_048_577,
                                 width=1, height=1, first_seen_at=NOW))


def test_la_identidad_puede_apuntar_a_su_copia_de_logo(clean_db):
    with Session(clean_db) as session:
        franchise = Franchise()
        logo = LogoImage(id="d" * 64, content=b"x", media_type="image/webp", size_bytes=1, width=1, height=1,
                         first_seen_at=NOW)
        session.add_all([franchise, logo])
        session.flush()
        session.add(Identity(franchise_id=franchise.id, short_name="[FICTICIO] A", valid_from=NOW,
                             logo_image_id=logo.id))
        session.commit()
        session.delete(logo)
        session.commit()
        # Borrar la copia deja la identidad sin logo, no la borra.
        assert session.scalars(select(Identity)).one().logo_image_id is None


def test_conjuntos_de_datos_de_la_lista_cerrada(clean_db):
    with Session(clean_db) as session:
        session.add(DatasetChange(dataset="matches", last_changed_at=NOW))
        session.commit()
    _rejects(clean_db, DatasetChange(dataset="noticias", last_changed_at=NOW))


def test_estado_de_fuente_por_fuente_y_tipo_de_consulta(clean_db):
    with Session(clean_db) as session:
        session.add_all([
            SourceState(source="bp", job="live", last_attempt_at=NOW, last_success_at=NOW, last_item_count=3),
            SourceState(source="bp", job="regular", last_attempt_at=NOW),
        ])
        session.commit()
    _rejects(clean_db, SourceState(source="bp", job="cada_minuto", last_attempt_at=NOW))
    _rejects(clean_db, SourceState(source="bp", job="live", last_attempt_at=NOW))  # repetida


def test_tareas_con_fecha_con_clave_unica(clean_db):
    with Session(clean_db) as session:
        session.add(SyncJob(key="history:champs:2026:+24h", kind="history", due_at=NOW))
        session.commit()
    _rejects(clean_db, SyncJob(key="history:champs:2026:+24h", kind="history", due_at=NOW))
    _rejects(clean_db, SyncJob(key="otra", kind="desconocida", due_at=NOW))


def test_una_sola_peticion_activa_por_fuente_e_historial(clean_db):
    # RF-107 y RF-108: nunca dos actualizaciones en curso de lo mismo, también a nivel de base de datos.
    with Session(clean_db) as session:
        session.add_all([
            SyncRequest(kind="source_refresh", source="bp", status="running", requested_at=NOW),
            SyncRequest(kind="source_refresh", source="wiki", status="pending", requested_at=NOW),
            SyncRequest(kind="history_reread", source=None, status="pending", requested_at=NOW),
            # Las terminadas no cuentan como activas.
            SyncRequest(kind="source_refresh", source="bp", status="done", result="success", requested_at=NOW),
        ])
        session.commit()
    _rejects(clean_db, SyncRequest(kind="source_refresh", source="bp", status="pending", requested_at=NOW))
    _rejects(clean_db, SyncRequest(kind="history_reread", source=None, status="running", requested_at=NOW))
    _rejects(clean_db, SyncRequest(kind="source_refresh", source="bp", status="done", result="empate",
                                   requested_at=NOW))


def test_registro_de_consultas_con_resultados_cerrados(clean_db):
    with Session(clean_db) as session:
        session.add(SyncRun(source="wiki", job="history", started_at=NOW, finished_at=NOW, outcome="partial",
                            message="3 datos rechazados"))
        session.commit()
    _rejects(clean_db, SyncRun(source="wiki", job="history", started_at=NOW, finished_at=NOW, outcome="regular"))


def test_incidencia_unica_aunque_falten_campos_y_con_repeticiones_por_dia(clean_db):
    # RF-147: una incidencia idéntica no crea otra fila, también si no tiene fuente ni valor.
    with Session(clean_db) as session:
        incident = Incident(source=None, kind="origin_blocked", subject="203.0.113.7", value_hash=None,
                            reason="5 intentos fallidos", first_at=NOW, last_at=NOW, repetitions=1)
        session.add(incident)
        session.flush()
        session.add(IncidentDay(incident_id=incident.id, day=date(2026, 9, 23), repetitions=1))
        session.commit()
    _rejects(clean_db, Incident(source=None, kind="origin_blocked", subject="203.0.113.7", value_hash=None,
                                reason="5 intentos fallidos", first_at=NOW, last_at=NOW, repetitions=1))
    _rejects(clean_db, Incident(source="bp", kind="rumor", subject="x", reason="y", first_at=NOW, last_at=NOW,
                                repetitions=1))
    _rejects(clean_db, Incident(source="bp", kind="data_rejected", subject="x", reason="y", first_at=NOW,
                                last_at=NOW, repetitions=0))


def test_resumen_diario_uno_por_dia(clean_db):
    with Session(clean_db) as session:
        session.add(DailySummary(day=date(2026, 9, 23), content={"bp": {"failed": 1}}, created_at=NOW))
        session.commit()
    _rejects(clean_db, DailySummary(day=date(2026, 9, 23), content={}, created_at=NOW))


# --- T-013 y T-014: administración ----------------------------------------------------------


def test_solo_existe_una_cuenta_de_administrador(clean_db):
    with Session(clean_db) as session:
        session.add(AdminUser(username="hugo", password_hash="$argon2id$...", created_at=NOW))
        session.commit()
        assert session.scalars(select(AdminUser)).one().id == 1
    _rejects(clean_db, AdminUser(id=2, username="otra", password_hash="$argon2id$...", created_at=NOW))
    _rejects(clean_db, AdminUser(username="otra", password_hash="$argon2id$...", created_at=NOW))


def test_sesiones_y_origenes_de_acceso(clean_db):
    with Session(clean_db) as session:
        session.add(AdminSession(token_hash="e" * 64, created_at=NOW, expires_at=NOW + timedelta(hours=8),
                                 last_seen_at=NOW, origin="203.0.113.7"))
        session.add(LoginOrigin(origin="203.0.113.7", failures=5, blocked_until=NOW + timedelta(minutes=15),
                                updated_at=NOW))
        session.commit()
        assert session.scalar(select(func.count()).select_from(AdminSession)) == 1
    _rejects(clean_db, LoginOrigin(origin="198.51.100.1", failures=-1, updated_at=NOW))


def test_los_modelos_de_la_002_siguen_funcionando_con_las_columnas_nuevas(clean_db):
    with Session(clean_db) as session:
        season = Season(year=2026, name="CDL 2026", started_at=NOW, changed_at=NOW)
        franchise = Franchise()
        session.add_all([season, franchise])
        session.flush()
        event = Event(season_id=season.id, name="[FICTICIO] Major 1", changed_at=NOW)
        player = Player(current_gamertag="[FICTICIO] J", changed_at=NOW)
        session.add_all([event, player])
        session.flush()
        match = Match(event_id=event.id, best_of=5, status="finished", stats_complete_at=NOW, changed_at=NOW)
        session.add(match)
        session.flush()
        match_map = MatchMap(match_id=match.id, position=1, played=True, changed_at=NOW)
        session.add(match_map)
        session.flush()
        session.add_all([
            PlayerMapStats(map_id=match_map.id, player_id=player.id, kills=10, changed_at=NOW),
            Standing(season_id=season.id, franchise_id=franchise.id, position=1, points=100, changed_at=NOW),
        ])
        session.commit()
        assert session.scalar(select(func.count()).select_from(Placement)) == 0
