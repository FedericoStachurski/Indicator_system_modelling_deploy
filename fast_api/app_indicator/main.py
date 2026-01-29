from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .core.config import STATIC_DIR
from .routers.health import router as health_router
from .routers.pages import router as pages_router
from .routers.simulate import router as simulate_router


def create_app() -> FastAPI:
    app = FastAPI(title="Soil Index Dashboard API")

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(health_router)
    app.include_router(pages_router)
    app.include_router(simulate_router)

    return app


app = create_app()

