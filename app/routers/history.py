# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.scan import ScanRecord
from app.schemas import ScanListResponse, ScanRecordResponse, Severity
from app.services.history import record_to_response

router = APIRouter(prefix="/scans", tags=["history"])


@router.get("")
async def list_scans(
    session: Annotated[AsyncSession, Depends(get_session)],
    severity: Severity | None = None,
    source: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ScanListResponse:
    stmt = select(ScanRecord)
    count_stmt = select(func.count()).select_from(ScanRecord)

    if severity is not None:
        stmt = stmt.where(ScanRecord.severity == severity.value)
        count_stmt = count_stmt.where(ScanRecord.severity == severity.value)
    if source is not None:
        stmt = stmt.where(ScanRecord.source == source)
        count_stmt = count_stmt.where(ScanRecord.source == source)

    stmt = stmt.order_by(
        ScanRecord.created_at.desc(), ScanRecord.id.desc()
    ).limit(limit).offset(offset)

    records = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar_one()

    return ScanListResponse(
        items=[record_to_response(r) for r in records],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{scan_id}")
async def get_scan(
    scan_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScanRecordResponse:
    record = await session.get(ScanRecord, scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return record_to_response(record)
