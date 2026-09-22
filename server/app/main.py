from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.container import Container
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.settings = settings
    app.state.container = Container(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
