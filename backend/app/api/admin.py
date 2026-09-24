"""Rutas de administración `/api/admin` (spec 003: RF-97 a RF-154; plan §3.4, §9, D-10, D-11).

- Todas, salvo `login`, exigen una sesión abierta: sin ella responden 401 (RF-137, RF-139).
- Toda petición que cambia algo (también `login` y `logout`) exige la cabecera
  `X-Retake-Admin: 1` y venir del mismo origen (D-11): una web ajena no puede usar la sesión.
- Los textos recibidos de las fuentes se devuelven tal cual, como texto plano recortado a 500
  caracteres (ya se guardan así); nunca se traducen (RF-118 a RF-120).
"""

import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin import origins, sessions
from app.admin.accounts import verify_login
from app.api.deps import get_clock, get_session
from app.config import get_settings
from app.db.models import AdminUser, DailySummary, Incident, Match, SourceState, SyncRequest, SyncRun
from app.domain.freshness import is_source_stopped, shortest_cycle
from app.domain.vocabulary import RETENTION, SESSION_DURATION, SUMMARY_TIMEZONE

router = APIRouter(prefix="/api/admin")

SOURCE_ORDER = ("bp", "wiki", "cdl")
# Por qué no se puede pedir una actualización de cada fuente (RF-110, RF-111).
NOT_REFRESHABLE = {
    "wiki": "La Wiki no se consulta: sus datos se importan con `uv run retake import-wiki-csv` (C-19).",
    "cdl": "La web oficial de la CDL está en reserva, sin conector (plan I-4).",
}
WRONG_CREDENTIALS = "Usuario o contraseña incorrectos."
BLOCKED = "Demasiados intentos fallidos desde este origen. Vuelve a intentarlo más tarde."


def trusted_proxy() -> str | None:
    """Proxy de confianza cuya cabecera `X-Forwarded-For` se acepta (plan D-10)."""
    return get_settings().trusted_proxy


def utc(value: datetime | None) -> str | None:
    """Fecha y hora ISO 8601 en UTC, con `Z`, como el resto de la API."""
    return None if value is None else value.astimezone(UTC).isoformat().replace("+00:00", "Z")


# --- Dependencias ------------------------------------------------------------------------------


def same_origin(request: Request) -> None:
    """Protección contra peticiones falsificadas (D-11, RF-139): cabecera propia y mismo origen."""
    if request.headers.get("x-retake-admin") != "1":
        raise HTTPException(status_code=403, detail="Petición no permitida.")
    sent = request.headers.get("origin") or request.headers.get("referer")
    if not sent or urlsplit(sent).netloc != request.headers.get("host"):
        raise HTTPException(status_code=403, detail="Petición no permitida.")


def admin_session(request: Request, session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Sesión abierta del administrador, o 401 (RF-137, RF-139)."""
    row = sessions.valid_session(session, request.cookies.get(sessions.COOKIE_NAME), clock.now())
    session.commit()
    if row is None:
        raise HTTPException(status_code=401, detail="Sesión no válida o caducada.")
    return row


# --- Acceso ------------------------------------------------------------------------------------


class Credentials(BaseModel):
    username: str
    password: str


@router.post("/login", dependencies=[Depends(same_origin)])
def login(credentials: Credentials, request: Request, session: Session = Depends(get_session),
          clock=Depends(get_clock)):
    """Usuario y contraseña → sesión en cookie (RF-124 a RF-133)."""
    now = clock.now()
    origin = origins.client_origin(request.client.host if request.client else None,
                                   request.headers.get("x-forwarded-for"), trusted_proxy())
    if origins.is_blocked(session, origin, now):
        session.commit()
        return JSONResponse({"detail": BLOCKED}, status_code=429)
    if not verify_login(session, credentials.username, credentials.password):
        origins.record_failure(session, origin, now)
        session.commit()
        return JSONResponse({"detail": WRONG_CREDENTIALS}, status_code=401)
    origins.record_success(session, origin, now)
    token = sessions.open_session(session, now, origin)
    session.commit()
    response = JSONResponse({"username": credentials.username})
    response.set_cookie(
        sessions.COOKIE_NAME, token, max_age=int(SESSION_DURATION.total_seconds()), path=sessions.COOKIE_PATH,
        httponly=True, samesite="strict", secure=get_settings().session_cookie_secure,
    )
    return response


@router.post("/logout", status_code=204, dependencies=[Depends(same_origin)])
def logout(request: Request, _=Depends(admin_session), session: Session = Depends(get_session)):
    """Cierra la sesión en el servidor (RF-138)."""
    sessions.close_session(session, request.cookies.get(sessions.COOKIE_NAME))
    session.commit()
    response = Response(status_code=204)
    response.delete_cookie(sessions.COOKIE_NAME, path=sessions.COOKIE_PATH)
    return response


@router.get("/me")
def me(_=Depends(admin_session), session: Session = Depends(get_session)):
    """Si hay una sesión abierta, y de quién (RF-124)."""
    user = session.get(AdminUser, 1)
    return {"username": user.username if user else None}


# --- Fuentes y peticiones ------------------------------------------------------------------------


def _request_out(req: SyncRequest, already_running: bool = False) -> dict:
    return {
        "id": str(req.id), "source": req.source, "status": req.status, "result": req.result,
        "incidentCount": req.incident_count, "message": req.message, "alreadyRunning": already_running,
        "requestedAt": utc(req.requested_at), "finishedAt": utc(req.finished_at),
        "logUrl": f"/api/admin/log?source={req.source}",
    }


@router.get("/sources")
def sources(_=Depends(admin_session), session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Por fuente: última consulta, última con éxito, si está parada y peticiones en curso (RF-103, RF-112 a RF-114)."""
    now = clock.now()
    live_active = session.scalar(select(Match.id).where(Match.status == "live").limit(1)) is not None
    result = []
    for source in SOURCE_ORDER:
        attempt, success = session.execute(
            select(func.max(SourceState.last_attempt_at), func.max(SourceState.last_success_at))
            .where(SourceState.source == source)).one()
        active = session.scalar(select(SyncRequest).where(SyncRequest.source == source,
                                                          SyncRequest.status.in_(("pending", "running"))))
        manual = source == "wiki"
        result.append({
            "source": source,
            "lastAttemptAt": utc(attempt),
            "lastSuccessAt": utc(success),  # para la Wiki, su última importación (C-19)
            "stopped": False if source == "cdl" else is_source_stopped(source, attempt, now, live_active),
            "cycleSeconds": None if manual or source == "cdl" else int(shortest_cycle(source, live_active).total_seconds()),
            "refreshable": source not in NOT_REFRESHABLE,
            "reason": NOT_REFRESHABLE.get(source),
            "activeRequest": _request_out(active) if active else None,
        })
    return result


@router.post("/sources/{source}/refresh", dependencies=[Depends(same_origin)])
def refresh(source: str, _=Depends(admin_session), session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Pide actualizar una fuente sin esperar al ciclo (RF-100, RF-107, RF-109 a RF-111)."""
    if source not in SOURCE_ORDER:
        raise HTTPException(status_code=404, detail="Fuente desconocida.")
    now = clock.now()
    if source in NOT_REFRESHABLE:
        req = SyncRequest(kind="source_refresh", source=source, status="done", result="forbidden",
                          message=NOT_REFRESHABLE[source], requested_at=now, finished_at=now)
        session.add(req)
        session.commit()
        return _request_out(req)
    active = session.scalar(select(SyncRequest).where(SyncRequest.kind == "source_refresh", SyncRequest.source == source,
                                                      SyncRequest.status.in_(("pending", "running"))))
    if active is not None:
        return _request_out(active, already_running=True)
    req = SyncRequest(kind="source_refresh", source=source, status="pending", requested_at=now)
    session.add(req)
    session.commit()
    return JSONResponse(_request_out(req), status_code=202)


@router.get("/requests/{request_id}")
def request_status(request_id: uuid.UUID, _=Depends(admin_session), session: Session = Depends(get_session)):
    """Estado y resultado de una petición, con su número de incidencias (RF-103 a RF-106)."""
    req = session.get(SyncRequest, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Petición no encontrada.")
    return _request_out(req)


# --- Registro y resúmenes ------------------------------------------------------------------------


@router.get("/log")
def log(_=Depends(admin_session), session: Session = Depends(get_session), clock=Depends(get_clock),
        source: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200, alias="pageSize")):
    """Registro de los últimos 7 días, paginado y filtrable por fuente (RF-140 a RF-149)."""
    since = clock.now() - RETENTION
    runs = select(SyncRun).where(SyncRun.finished_at >= since)
    incidents = select(Incident).where(Incident.last_at >= since)
    if source:
        runs, incidents = runs.where(SyncRun.source == source), incidents.where(Incident.source == source)
    offset = (page - 1) * page_size
    run_rows = session.scalars(runs.order_by(SyncRun.finished_at.desc(), SyncRun.id.desc())
                               .offset(offset).limit(page_size)).all()
    incident_rows = session.scalars(incidents.order_by(Incident.last_at.desc(), Incident.id.desc())
                                    .offset(offset).limit(page_size)).all()
    return {
        "page": page, "pageSize": page_size,
        "runs": [{"id": r.id, "source": r.source, "job": r.job, "outcome": r.outcome, "message": r.message,
                  "startedAt": utc(r.started_at), "finishedAt": utc(r.finished_at),
                  "requestId": str(r.request_id) if r.request_id else None} for r in run_rows],
        "incidents": [{"id": i.id, "source": i.source, "kind": i.kind, "subject": i.subject, "reason": i.reason,
                       "detail": i.detail, "repetitions": i.repetitions, "firstAt": utc(i.first_at),
                       "lastAt": utc(i.last_at)} for i in incident_rows],
    }


@router.get("/summaries")
def summaries(_=Depends(admin_session), session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Resúmenes diarios de los últimos 7 días, del más reciente al más antiguo (RF-150 a RF-154)."""
    today = clock.now().astimezone(ZoneInfo(SUMMARY_TIMEZONE)).date()
    rows = session.scalars(select(DailySummary).where(DailySummary.day >= today - timedelta(days=7))
                           .order_by(DailySummary.day.desc())).all()
    return [{"day": row.day, "content": row.content, "createdAt": utc(row.created_at)} for row in rows]
