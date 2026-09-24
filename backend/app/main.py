"""Aplicación FastAPI de Retake (plan de la spec 002, §1.4).

`create_app` construye la aplicación según el entorno: en producción no se publican
`/docs` ni `/openapi.json` (T-057).
"""

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import Engine, text

from app.api.admin import router as admin_router
from app.api.deps import engine_or_none
from app.api.routes import router
from app.config import get_settings

__all__ = ["app", "create_app", "engine_or_none"]


def health(engine: Engine | None = Depends(engine_or_none)) -> JSONResponse:
    """Estado del servicio y de la base de datos: 200 si la base de datos contesta, 503 si no."""
    database_ok = False
    if engine is not None:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            database_ok = True
        except Exception:  # noqa: BLE001
            database_ok = False
    body = {"status": "ok", "database": "ok" if database_ok else "unavailable"}
    return JSONResponse(body, status_code=200 if database_ok else 503)


class NoStoreApiMiddleware:
    """Las respuestas de `/api/` no se guardan en la caché del navegador (plan I-44 de la 003).

    Safari devolvía una copia guardada de `/api/matches` y el bloque en vivo no cambiaba sin
    recargar (RF-79, RF-82). Solo se añade si la ruta no fija su propio `Cache-Control`: los logos
    (inmutables, por su huella) y el canal de eventos conservan el suyo. Es un middleware ASGI puro
    para no interferir con el canal de eventos, que es una respuesta sin fin.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            return await self.app(scope, receive, send)

        async def send_with_header(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers") or [])
                if not any(name.lower() == b"cache-control" for name, _ in headers):
                    headers.append((b"cache-control", b"no-store"))
                message = {**message, "headers": headers}
            await send(message)

        return await self.app(scope, receive, send_with_header)


def create_app(app_env: str | None = None) -> FastAPI:
    """Construye la aplicación; `app_env` sustituye al de la configuración (útil en pruebas)."""
    env = app_env or get_settings().app_env
    public_docs = env != "production"
    application = FastAPI(
        title="Retake API",
        version="0.1.0",
        docs_url="/docs" if public_docs else None,
        redoc_url="/redoc" if public_docs else None,
        openapi_url="/openapi.json" if public_docs else None,
    )
    application.add_api_route("/api/health", health, methods=["GET"])
    application.include_router(router)
    application.include_router(admin_router)  # spec 003, F7
    application.add_middleware(NoStoreApiMiddleware)  # spec 003, I-44
    return application


app = create_app()
