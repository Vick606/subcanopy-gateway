# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_scanner_service
from app.schemas import ScanRequest, ScanResponse
from app.services.scanner import ScannerService

router = APIRouter(tags=["scan"])


@router.post("/scan")
async def scan(
    request: ScanRequest,
    service: Annotated[ScannerService, Depends(get_scanner_service)],
) -> ScanResponse:
    return service.scan(request.text, source=request.source)
