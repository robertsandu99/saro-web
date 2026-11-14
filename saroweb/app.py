from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from saroweb.apis import health_api, player_api, squad_api, team_api
from saroweb.settings import get_settings
from saroweb.utils.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)


def _register_exception_handlers(app: FastAPI) -> None:
    """Convert domain exceptions into proper HTTP responses.
    Services raise domain errors; this layer converts them to HTTP.
    """

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=400, content={"detail": exc.message})


def _register_routers(app: FastAPI) -> None:
    app.include_router(health_api.router)
    app.include_router(squad_api.router)
    app.include_router(player_api.router)
    app.include_router(team_api.router)


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Sports and games web platform",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    _register_exception_handlers(app)
    _register_routers(app)

    return app


app = create_app()
