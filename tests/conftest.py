# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from collections.abc import AsyncIterator, Iterator

import psycopg
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.database import get_session
from app.main import create_app

TEST_DATABASE_URL = "postgresql+psycopg://scg:scg@localhost:5432/scg_test"
TEST_DATABASE_SYNC_URL = "postgresql://scg:scg@localhost:5432/scg_test"
TEST_ADMIN_URL = "postgresql://scg:scg@localhost:5432/postgres"


def _ensure_test_database() -> None:
    """Create scg_test if it does not exist."""
    with psycopg.connect(
        TEST_ADMIN_URL, autocommit=True
    ) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", ("scg_test",)
        )
        if cur.fetchone() is None:
            cur.execute('CREATE DATABASE "scg_test"')


def _run_migrations() -> None:
    """Apply Alembic migrations to the test database."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def migrated_db() -> Iterator[None]:
    _ensure_test_database()
    _run_migrations()
    yield


@pytest.fixture(scope="session")
def _sync_conn(migrated_db: None) -> Iterator[psycopg.Connection]:
    """Session-scoped sync connection for table cleanup."""
    with psycopg.connect(TEST_DATABASE_SYNC_URL, autocommit=True) as conn:
        yield conn


@pytest.fixture(autouse=True)
def _truncate_scan_records(
    _sync_conn: psycopg.Connection,
) -> Iterator[None]:
    """Empty scan_records before each test.

    The sync TestClient tests use the app's real engine and commit for
    real, so rows accumulate. This fixture resets between tests.
    """
    with _sync_conn.cursor() as cur:
        cur.execute("TRUNCATE scan_records")
    yield


@pytest_asyncio.fixture(scope="session")
async def test_engine(migrated_db: None) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Session bound to an outer transaction that rolls back per test.

    join_transaction_mode=create_savepoint means session.commit() inside
    the route releases a savepoint, not the outer transaction. The outer
    rollback still discards everything.
    """
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            async with factory() as session:
                yield session
        finally:
            await transaction.rollback()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        debug=True,
        log_level="DEBUG",
        database_url=TEST_DATABASE_URL,
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings=settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def db_client(
    app: FastAPI, db_session: AsyncSession
) -> AsyncIterator[AsyncClient]:
    """AsyncClient that shares a session with the test.

    The route and the assertion run in the same event loop and on the
    same connection, so the test sees uncommitted writes from the route.
    """

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
