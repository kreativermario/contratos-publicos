"""Application factory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from contratos_core import Database, Settings, get_settings

from .caching import cache_control_for
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routers import (companies, contracts, meta, municipalities, rankings,
                      suppliers)

log = logging.getLogger("contratos.api")

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.database = Database(settings)
        app.state.settings = settings
        log.info("connected to postgres")
        yield
        app.state.database.dispose()

    app = FastAPI(title="Onde Vai Parar", version="0.1.0", lifespan=lifespan,
                  root_path=settings.api_root_path,
                  description="Contratos públicos portugueses, lidos com má-língua "
                              "mas com os números certos.")
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.api_cors_origins,
        allow_methods=["GET"], allow_headers=["*"],
    )

    @app.middleware("http")
    async def cache_headers(request: Request, call_next):
        # ponytail: the CDN is the cache. Redis only if hot keys ever outgrow a
        # header, which for a dataset that moves once a night they will not.
        response = await call_next(request)
        response.headers["Cache-Control"] = cache_control_for(
            request.method, response.status_code, request.url.path, settings)
        return response

    app.include_router(meta.health_router)
    version = settings.api_version_prefix
    app.include_router(companies.router, prefix=version)
    app.include_router(contracts.router, prefix=version)
    app.include_router(meta.router, prefix=version)
    app.include_router(municipalities.router, prefix=version)
    app.include_router(rankings.router, prefix=version)
    app.include_router(suppliers.router, prefix=version)
    return app


app = create_app()
