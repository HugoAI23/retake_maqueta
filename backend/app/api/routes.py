"""Rutas de solo lectura de los datos de la liga (plan de la spec 002, §1.4 y D-11)."""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.api import schemas as out
from app.api import views
from app.api.deps import engine_or_none, get_clock, get_session
from app.api.freshness import freshness as freshness_of
from app.api.stream import event_stream, pg_notifications
from app.db.models import LogoImage, Match, Player
from app.db.queries import current_season

router = APIRouter(prefix="/api")


@router.get("/season/current", response_model=out.SeasonOut)
def season_current(session: Session = Depends(get_session)):
    """Temporada actual; 404 si ninguna ha empezado todavía (RF-2, RF-3, RF-52)."""
    season = current_season(session)
    if season is None:
        raise HTTPException(status_code=404, detail="Todavía no ha empezado ninguna temporada.")
    return views.season_view(season)


@router.get("/franchises", response_model=list[out.FranchiseOut])
def franchises(session: Session = Depends(get_session)):
    """Franquicias con todas sus identidades, de la más antigua a la vigente (RF-10, RF-11, RF-74)."""
    return views.franchise_views(session)


@router.get("/players", response_model=list[out.PlayerOut])
def players(session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Jugadores de la temporada actual y del historial, sin fecha de nacimiento (RF-24)."""
    return views.player_views(session, clock.now())


@router.get("/players/{player_id}", response_model=out.PlayerOut)
def player(player_id: uuid.UUID, session: Session = Depends(get_session), clock=Depends(get_clock)):
    found = session.get(Player, player_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Jugador no encontrado.")
    return views.player_view(session, found, clock.now())


@router.get("/events", response_model=list[out.EventOut])
def events(session: Session = Depends(get_session)):
    """Eventos de la temporada actual, con su nombre tal como se publica (RF-30, RF-61)."""
    return views.event_views(session)


@router.get("/matches", response_model=list[out.MatchOut])
def matches(session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Partidos de la temporada actual, por fecha y hora de inicio."""
    return views.match_views(session, clock.now())


@router.get("/matches/{match_id}", response_model=out.MatchOut)
def match(match_id: uuid.UUID, session: Session = Depends(get_session), clock=Depends(get_clock)):
    found = session.get(Match, match_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Partido no encontrado.")
    return views.match_view(session, found, clock.now())


@router.get("/standings", response_model=list[out.StandingOut])
def standings(session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Tabla de posiciones de la temporada actual, tal como se publica (RF-49, RF-50, RF-122)."""
    return views.standing_views(session, clock.now())


@router.get("/championships", response_model=list[out.ChampionshipOut])
def championships(session: Session = Depends(get_session)):
    """Historial de campeonatos mundiales terminados (RF-4, RF-55)."""
    return views.championship_views(session)


# --- Spec 003 (F6) -------------------------------------------------------------------------------


@router.get("/freshness", response_model=dict[str, out.FreshnessOut])
def freshness(session: Session = Depends(get_session), clock=Depends(get_clock)):
    """Último cambio y si está sin actualizar, por conjunto de datos (RF-89, RF-155, RF-158; C-20)."""
    return freshness_of(session, clock.now())


SHA256 = re.compile(r"^[0-9a-f]{64}$")


@router.get("/logos/{logo_id}")
def logo(logo_id: str, session: Session = Depends(get_session)):
    """Copia propia de un logo con su tipo real, sin adivinar el tipo y con caché larga (RF-65 a RF-71).

    La huella SHA-256 identifica el contenido, así que la respuesta no cambia nunca (`immutable`).
    """
    image = session.get(LogoImage, logo_id) if SHA256.match(logo_id) else None
    if image is None:
        raise HTTPException(status_code=404, detail="Logo no encontrado.")
    return Response(content=image.content, media_type=image.media_type, headers={
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "public, max-age=31536000, immutable",
    })


@router.get("/stream")
async def stream(request: Request, engine: Engine | None = Depends(engine_or_none), clock=Depends(get_clock)):
    """Canal de eventos del servidor: `change`, `freshness` y latido (RF-79 a RF-81, RF-89; plan §3.3)."""
    if engine is None:
        raise HTTPException(status_code=503, detail="La base de datos no está disponible.")
    conninfo = engine.url.set(drivername="postgresql").render_as_string(hide_password=False)

    def stale_by_dataset() -> dict[str, bool]:
        with Session(engine) as session:
            return {dataset: entry["stale"] for dataset, entry in freshness_of(session, clock.now()).items()}

    return StreamingResponse(
        event_stream(pg_notifications(conninfo), stale_by_dataset, clock, is_disconnected=request.is_disconnected),
        media_type="text/event-stream",
        # Sin caché ni búfer en proxies, para que cada evento llegue en el momento (plan §10, "SSE y proxies").
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
