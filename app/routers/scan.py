# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import get_session
from app.dependencies import (
    get_app_settings,
    get_embedding_service,
    get_scanner_service,
)
from app.schemas import (
    BatchScanRequest,
    BatchScanResponse,
    ScanRequest,
    ScanResponse,
)
from app.services.embedding import EmbeddingService
from app.services.history import save_scan
from app.services.scanner import ScannerService
from app.services.similarity import find_nearest

router = APIRouter(tags=["scan"])


@router.post("/scan")
async def scan(
    request: ScanRequest,
    service: Annotated[ScannerService, Depends(get_scanner_service)],
    embedder: Annotated[EmbeddingService, Depends(get_embedding_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ScanResponse:
    result = service.scan(request.text, source=request.source)
    embedding = await embedder.embed(request.text)
    match = await find_nearest(session, embedding, settings.similarity_threshold)
    result = result.model_copy(update={"nearest_match": match})
    await save_scan(session, request.text, result)
    return result


@router.post("/scan/batch")
async def scan_batch(
    request: BatchScanRequest,
    service: Annotated[ScannerService, Depends(get_scanner_service)],
    embedder: Annotated[EmbeddingService, Depends(get_embedding_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> BatchScanResponse:
    batch = service.scan_batch(request.texts, source=request.source)
    embeddings = await embedder.embed_batch(request.texts)

    enriched = []
    for text, result, embedding in zip(
        request.texts, batch.results, embeddings, strict=True
    ):
        match = await find_nearest(
            session, embedding, settings.similarity_threshold
        )
        result = result.model_copy(update={"nearest_match": match})
        await save_scan(session, text, result)
        enriched.append(result)

    return BatchScanResponse(results=enriched)
