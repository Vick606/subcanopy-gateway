# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from subcanopy_guard import ContextScanner

from app.config import Settings
from app.database import get_session
from app.models.api_key import APIKey
from app.security import hash_api_key
from app.services.embedding import EmbeddingService
from app.services.scanner import ScannerService

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@lru_cache(maxsize=1)
def get_scanner_service() -> ScannerService:
    return ScannerService(ContextScanner())


def get_embedding_service(request: Request) -> EmbeddingService:
    service: EmbeddingService | None = getattr(
        request.app.state, "embedding_service", None
    )
    if service is None:
        raise RuntimeError(
            "Embedding service is not initialized. "
            "The app must be created with with_embedding_model=True."
        )
    return service


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def require_api_key(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    api_key: Annotated[str | None, Security(api_key_header)],
) -> APIKey:
    """Verify the X-API-Key header against the api_keys table.

    Returns the matched row and stores its identity on request.state
    for logging and rate limiting. Raises 401 on missing, invalid,
    inactive, or expired keys.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "APIKey"},
        )

    key_hash = hash_api_key(api_key, settings.api_key_pepper.encode())
    stmt = select(APIKey).where(
        APIKey.key_hash == key_hash,
        APIKey.is_active.is_(True),
    )
    record = (await session.execute(stmt)).scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    now = datetime.now(UTC)
    if record.expires_at is not None and record.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired",
            headers={"WWW-Authenticate": "APIKey"},
        )

    record.last_used_at = now
    await session.commit()

    request.state.api_key_id = record.id
    request.state.api_key_name = record.name

    return record
