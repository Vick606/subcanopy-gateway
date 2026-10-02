# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.database import create_engine, create_session_factory
from app.routers.history import router as history_router
from app.routers.scan import router as scan_router
from app.services.embedding import EmbeddingService, load_model


def create_app(
    settings: Settings | None = None,
    *,
    with_embedding_model: bool = True,
) -> FastAPI:
    settings = settings or get_settings()

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if with_embedding_model:
            model = await asyncio.to_thread(
                load_model, settings.embedding_model
            )
            app.state.embedding_service = EmbeddingService(model)
        yield
        await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    async def version() -> dict[str, str]:
        return {"app": settings.app_name, "version": settings.version}

    app.include_router(scan_router)
    app.include_router(history_router)

    return app
