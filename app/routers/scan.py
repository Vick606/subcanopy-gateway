# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_scanner_service
from app.schemas import (
    BatchScanRequest,
    BatchScanResponse,
    ScanRequest,
    ScanResponse,
)
from app.services.history import save_scan
from app.services.scanner import ScannerService

router = APIRouter(tags=["scan"])


@router.post("/scan")
async def scan(
    request: ScanRequest,
    service: Annotated[ScannerService, Depends(get_scanner_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScanResponse:
    result = service.scan(request.text, source=request.source)
    await save_scan(session, request.text, result)
    return result


@router.post("/scan/batch")
async def scan_batch(
    request: BatchScanRequest,
    service: Annotated[ScannerService, Depends(get_scanner_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BatchScanResponse:
    batch = service.scan_batch(request.texts, source=request.source)
    for text, result in zip(request.texts, batch.results, strict=True):
        await save_scan(session, text, result)
    return batch
