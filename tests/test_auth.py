# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import require_api_key
from app.models.api_key import APIKey
from app.security import generate_api_key, hash_api_key

PEPPER = "test-pepper-at-least-32-bytes-long!"


def _make_settings() -> Settings:
    return Settings(
        debug=True,
        log_level="DEBUG",
        database_url="postgresql+psycopg://scg:scg@localhost:5432/scg_test",
        api_key_pepper=PEPPER,
    )


async def _insert_key(
    session: AsyncSession,
    raw_key: str,
    *,
    is_active: bool = True,
    expires_at: datetime | None = None,
) -> APIKey:
    record = APIKey(
        id=uuid.uuid4(),
        name="test-key",
        key_hash=hash_api_key(raw_key, PEPPER.encode()),
        is_active=is_active,
        expires_at=expires_at,
    )
    session.add(record)
    await session.commit()
    return record


@pytest.fixture
def authed_app(app: FastAPI) -> FastAPI:
    """Remove the auth bypass so require_api_key actually runs."""
    app.dependency_overrides.pop(require_api_key, None)
    return app


@pytest.mark.asyncio
async def test_health_is_public(
    db_client: AsyncClient, authed_app: FastAPI
) -> None:
    response = await db_client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_version_requires_key(
    db_client: AsyncClient, authed_app: FastAPI
) -> None:
    response = await db_client.get("/version")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_requires_key(
    db_client: AsyncClient, authed_app: FastAPI
) -> None:
    response = await db_client.post("/scan", json={"text": "hello"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_rejects_invalid_key(
    db_client: AsyncClient, authed_app: FastAPI
) -> None:
    response = await db_client.post(
        "/scan",
        json={"text": "hello"},
        headers={"X-API-Key": "scg_invalid"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_accepts_valid_key(
    db_client: AsyncClient,
    authed_app: FastAPI,
    db_session: AsyncSession,
) -> None:
    raw_key = generate_api_key()
    await _insert_key(db_session, raw_key)

    response = await db_client.post(
        "/scan",
        json={"text": "hello"},
        headers={"X-API-Key": raw_key},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_scan_rejects_inactive_key(
    db_client: AsyncClient,
    authed_app: FastAPI,
    db_session: AsyncSession,
) -> None:
    raw_key = generate_api_key()
    await _insert_key(db_session, raw_key, is_active=False)

    response = await db_client.post(
        "/scan",
        json={"text": "hello"},
        headers={"X-API-Key": raw_key},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_rejects_expired_key(
    db_client: AsyncClient,
    authed_app: FastAPI,
    db_session: AsyncSession,
) -> None:
    raw_key = generate_api_key()
    await _insert_key(
        db_session,
        raw_key,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )

    response = await db_client.post(
        "/scan",
        json={"text": "hello"},
        headers={"X-API-Key": raw_key},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_updates_last_used_at(
    db_client: AsyncClient,
    authed_app: FastAPI,
    db_session: AsyncSession,
) -> None:
    raw_key = generate_api_key()
    record = await _insert_key(db_session, raw_key)

    assert record.last_used_at is None

    await db_client.post(
        "/scan",
        json={"text": "hello"},
        headers={"X-API-Key": raw_key},
    )

    await db_session.refresh(record)
    assert record.last_used_at is not None


@pytest.mark.asyncio
async def test_history_requires_key(
    db_client: AsyncClient, authed_app: FastAPI
) -> None:
    response = await db_client.get("/scans")

    assert response.status_code == 401
