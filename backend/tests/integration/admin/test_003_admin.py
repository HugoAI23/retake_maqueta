"""F7 · Administración en el servidor (spec 003: RF-100 a RF-154; plan §3.4, §9, D-10 a D-12, H-7, H-8).

Las contraseñas de estas pruebas son ficticias y solo existen aquí; la real la crea Hugo con
`retake set-admin-password` y nunca pasa por el código ni por los documentos.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import cli
from app.admin.accounts import set_admin_password, verify_login
from app.api.deps import get_clock
from app.clock import FixedClock
from app.db.models import (
    AdminSession,
    AdminUser,
    DailySummary,
    Incident,
    LoginOrigin,
    SourceState,
    SyncRequest,
    SyncRun,
)
from app.main import app, engine_or_none

NOW = datetime(2026, 12, 5, 20, 0, tzinfo=UTC)
USER, PASSWORD = "hugo-de-prueba", "contraseña-ficticia-de-prueba"
ORIGIN = "http://testserver"
SAFE = {"X-Retake-Admin": "1", "Origin": ORIGIN}


@pytest.fixture
def db(clean_db):
    with Session(clean_db) as session:
        yield session


@pytest.fixture
def admin(clean_db, db):
    set_admin_password(db, USER, PASSWORD, NOW)
    db.commit()
    clock = FixedClock(NOW)
    app.dependency_overrides[engine_or_none] = lambda: clean_db
    app.dependency_overrides[get_clock] = lambda: clock
    with TestClient(app) as client:
        client.clock = clock
        yield client
    app.dependency_overrides.clear()


def login(client, username=USER, password=PASSWORD, headers=SAFE, client_ip=None):
    extra = {"X-Forwarded-For": client_ip} if client_ip else {}
    return client.post("/api/admin/login", json={"username": username, "password": password}, headers={**headers, **extra})


# --- T-064 · cuenta única con Argon2id ------------------------------------------------------------


def test_solo_se_guarda_un_hash_argon2id(db):
    set_admin_password(db, USER, PASSWORD, NOW)
    db.commit()
    (user,) = db.scalars(select(AdminUser)).all()
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash
    assert verify_login(db, USER, PASSWORD) and not verify_login(db, USER, "otra")


def test_cambiar_la_contrasena_mantiene_una_sola_cuenta_y_cierra_las_sesiones(db):
    set_admin_password(db, USER, PASSWORD, NOW)
    db.add(AdminSession(token_hash="a" * 64, created_at=NOW, expires_at=NOW + timedelta(hours=8), last_seen_at=NOW))
    db.commit()
    set_admin_password(db, "otro-usuario", "otra-contraseña-ficticia", NOW)
    db.commit()
    assert db.scalar(select(func.count()).select_from(AdminUser)) == 1
    assert db.scalar(select(func.count()).select_from(AdminSession)) == 0


def test_la_base_de_datos_rechaza_una_segunda_cuenta(db):
    set_admin_password(db, USER, PASSWORD, NOW)
    db.commit()
    db.add(AdminUser(id=2, username="intruso", password_hash="x", created_at=NOW))
    with pytest.raises(IntegrityError):
        db.flush()


def test_la_orden_pide_la_contrasena_sin_mostrarla_y_nunca_por_argumento(clean_db, monkeypatch, capsys):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or USER)
    monkeypatch.setattr("getpass.getpass", lambda prompt: prompts.append(prompt) or PASSWORD)
    monkeypatch.setattr("app.db.engine.get_engine", lambda: clean_db)
    cli.main(["set-admin-password"])
    assert len(prompts) == 3  # usuario, contraseña y repetición
    assert PASSWORD not in capsys.readouterr().out
    with Session(clean_db) as session:
        assert verify_login(session, USER, PASSWORD)
    with pytest.raises(SystemExit):
        cli.main(["set-admin-password", "--password", PASSWORD])


def test_la_orden_rechaza_contrasenas_que_no_coinciden(clean_db, monkeypatch):
    answers = iter([PASSWORD, "distinta"])
    monkeypatch.setattr("builtins.input", lambda prompt: USER)
    monkeypatch.setattr("getpass.getpass", lambda prompt: next(answers))
    monkeypatch.setattr("app.db.engine.get_engine", lambda: clean_db)
    with pytest.raises(SystemExit):
        cli.main(["set-admin-password"])
    with Session(clean_db) as session:
        assert session.scalar(select(func.count()).select_from(AdminUser)) == 0


# --- T-065 · bloqueo por origen -------------------------------------------------------------------


def test_credenciales_incorrectas_sin_decir_cual(admin):
    wrong_user, wrong_password = login(admin, username="nadie"), login(admin, password="mala")
    assert wrong_user.status_code == wrong_password.status_code == 401
    assert wrong_user.json() == wrong_password.json()


def test_cinco_fallos_bloquean_el_origen_15_minutos_tambien_con_la_contrasena_correcta(admin, db):
    for attempt in range(5):
        login(admin, username="nadie" if attempt % 2 else USER, password="mala")
    assert login(admin).status_code == 429  # RF-129: bloqueado aunque la contraseña sea correcta
    incident = db.scalar(select(Incident).where(Incident.kind == "origin_blocked"))
    assert incident is not None  # RF-133
    admin.clock.set(NOW + timedelta(minutes=15, seconds=1))
    assert login(admin).status_code == 200


def test_el_bloqueo_no_afecta_a_otros_origenes(admin):
    for _ in range(5):
        login(admin, password="mala")
    assert login(admin).status_code == 429
    # Sin proxy de confianza, la cabecera X-Forwarded-For no cambia el origen (plan D-10).
    assert login(admin, client_ip="203.0.113.9").status_code == 429


def test_con_proxy_de_confianza_el_origen_es_el_de_su_cabecera(admin, monkeypatch):
    monkeypatch.setattr("app.api.admin.trusted_proxy", lambda: "testclient")
    for _ in range(5):
        login(admin, password="mala", client_ip="203.0.113.9")
    assert login(admin, client_ip="203.0.113.9").status_code == 429
    assert login(admin, client_ip="198.51.100.7").status_code == 200  # RF-130


def test_un_acceso_correcto_pone_a_cero_el_contador(admin, db):
    for _ in range(4):
        login(admin, password="mala")
    assert login(admin).status_code == 200
    for _ in range(4):
        login(admin, password="mala")
    assert login(admin).status_code == 200  # 4 + 4 fallos no bloquean: el contador volvió a cero


def test_al_acabar_el_bloqueo_el_contador_vuelve_a_cero(admin):
    for _ in range(5):
        login(admin, password="mala")
    admin.clock.set(NOW + timedelta(minutes=16))
    login(admin, password="mala")
    assert login(admin).status_code == 200  # un solo fallo tras el bloqueo no bloquea


# --- T-066 · sesiones -----------------------------------------------------------------------------


def test_la_sesion_va_en_una_cookie_segura_y_solo_se_guarda_su_huella(admin, db):
    response = login(admin)
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie.replace("Strict", "strict")
    assert "Path=/api/admin" in cookie and "Max-Age=28800" in cookie
    token = response.cookies.get("retake_admin")
    assert token and len(token) >= 43
    stored = db.scalars(select(AdminSession.token_hash)).all()
    assert token not in stored and len(stored[0]) == 64


def test_la_sesion_caduca_a_las_8_horas(admin):
    login(admin)
    assert admin.get("/api/admin/me").status_code == 200
    admin.clock.set(NOW + timedelta(hours=8, seconds=1))
    assert admin.get("/api/admin/me").status_code == 401


def test_cerrar_sesion_la_invalida_en_el_servidor(admin):
    response = login(admin)
    token = response.cookies.get("retake_admin")
    assert admin.post("/api/admin/logout", headers=SAFE).status_code == 204
    admin.cookies.set("retake_admin", token, path="/api/admin")
    assert admin.get("/api/admin/me").status_code == 401


def test_varias_sesiones_a_la_vez(admin, clean_db):
    first = login(admin).cookies.get("retake_admin")
    second = login(admin).cookies.get("retake_admin")
    for token in (first, second):
        admin.cookies.clear()
        admin.cookies.set("retake_admin", token, path="/api/admin")
        assert admin.get("/api/admin/me").json() == {"username": USER}


# --- T-067 · peticiones falsificadas --------------------------------------------------------------


@pytest.mark.parametrize("headers", [{"Origin": ORIGIN}, {"X-Retake-Admin": "1", "Origin": "https://ajeno.example"},
                                     {"X-Retake-Admin": "1"}])
def test_sin_cabecera_propia_o_desde_otro_origen_se_rechaza(admin, headers):
    assert login(admin, headers=headers).status_code == 403
    login(admin)
    assert admin.post("/api/admin/sources/bp/refresh", headers=headers).status_code == 403


# --- T-068 · rutas ------------------------------------------------------------------------------


@pytest.mark.parametrize(("method", "path"), [
    ("get", "/api/admin/me"), ("get", "/api/admin/sources"), ("post", "/api/admin/sources/bp/refresh"),
    ("get", f"/api/admin/requests/{uuid.uuid4()}"), ("get", "/api/admin/log"), ("get", "/api/admin/summaries"),
    ("post", "/api/admin/logout"),
])
def test_sin_sesion_todo_responde_401(admin, method, path):
    assert getattr(admin, method)(path, headers=SAFE).status_code == 401


def test_estado_de_las_fuentes(admin, db):
    db.add_all([SourceState(source="bp", job="regular", last_attempt_at=NOW - timedelta(hours=3),
                            last_success_at=NOW - timedelta(hours=4)),
                SourceState(source="wiki", job="history", last_attempt_at=NOW - timedelta(days=200),
                            last_success_at=NOW - timedelta(days=200))])
    db.commit()
    login(admin)
    sources = {s["source"]: s for s in admin.get("/api/admin/sources").json()}
    assert sources["bp"]["lastAttemptAt"] == "2026-12-05T17:00:00Z" and sources["bp"]["stopped"] is True
    assert sources["bp"]["refreshable"] is True
    assert sources["wiki"]["stopped"] is False and sources["wiki"]["refreshable"] is False  # C-19
    assert sources["wiki"]["lastSuccessAt"] == "2026-05-19T20:00:00Z"
    assert sources["cdl"]["refreshable"] is False  # en reserva, sin conector (I-4)


def test_pedir_una_actualizacion_y_ver_su_resultado(admin, db):
    login(admin)
    created = admin.post("/api/admin/sources/bp/refresh", headers=SAFE)
    assert created.status_code == 202
    request_id = created.json()["id"]
    again = admin.post("/api/admin/sources/bp/refresh", headers=SAFE)
    assert again.json()["id"] == request_id and again.json()["alreadyRunning"] is True  # RF-107, RF-109
    db.expire_all()
    req = db.get(SyncRequest, uuid.UUID(request_id))
    req.status, req.result, req.incident_count, req.finished_at = "done", "partial", 3, NOW
    db.commit()
    assert admin.get(f"/api/admin/requests/{request_id}").json()["result"] == "partial"
    assert admin.get(f"/api/admin/requests/{request_id}").json()["incidentCount"] == 3


def test_la_wiki_no_se_puede_actualizar_y_se_dice_el_motivo(admin):
    login(admin)
    body = admin.post("/api/admin/sources/wiki/refresh", headers=SAFE).json()
    assert body["result"] == "forbidden" and "import-wiki-csv" in body["message"]  # RF-110, RF-111, C-19


def test_una_fuente_desconocida_da_404(admin):
    login(admin)
    assert admin.post("/api/admin/sources/inventada/refresh", headers=SAFE).status_code == 404


def test_registro_paginado_filtrable_y_con_texto_plano(admin, db):
    db.add_all([SyncRun(source="bp", job="regular", started_at=NOW, finished_at=NOW, outcome="failure",
                        message="<b>503</b> Service Unavailable"),
                SyncRun(source="cdl", job="regular", started_at=NOW, finished_at=NOW, outcome="success"),
                Incident(source="bp", kind="query_failed", subject="regular", reason="<script>x</script>",
                         first_at=NOW, last_at=NOW, repetitions=4)])
    db.commit()
    login(admin)
    body = admin.get("/api/admin/log", params={"source": "bp"}).json()
    assert [run["message"] for run in body["runs"]] == ["<b>503</b> Service Unavailable"]
    assert body["incidents"][0]["reason"] == "<script>x</script>" and body["incidents"][0]["repetitions"] == 4
    assert len(admin.get("/api/admin/log", params={"pageSize": 1, "page": 2}).json()["runs"]) == 1
    assert admin.get("/api/admin/log", params={"pageSize": 1, "page": 3}).json()["runs"] == []


def test_resumenes_de_los_ultimos_7_dias(admin, db):
    for days in (1, 3, 9):
        day = (NOW - timedelta(days=days)).date()
        db.add(DailySummary(day=day, content={"total_incidents": days}, created_at=NOW))
    db.commit()
    login(admin)
    summaries = admin.get("/api/admin/summaries").json()
    assert [s["content"]["total_incidents"] for s in summaries] == [1, 3]
