# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import hashlib
import uuid

import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack import AttackPattern
from app.models.scan import ScanRecord
from app.schemas import (
    NearestMatch,
    ScanResponse,
    Severity,
    SignalBreakdown,
)
from app.services.history import (
    hash_text,
    preview_text,
    record_to_response,
    save_scan,
)


def _response(severity: Severity = Severity.HIGH) -> ScanResponse:
    return ScanResponse(
        severity=severity,
        risk=0.78,
        source="tool_output",
        blocking=True,
        matches=["density=0.62"],
        hotspots=[(10, 25)],
        signals=SignalBreakdown(
            density_risk=0.62,
            discontinuity_risk=0.15,
            provenance_multiplier=1.35,
        ),
    )


def test_hash_text_matches_sha256() -> None:
    assert hash_text("hello") == hashlib.sha256(b"hello").hexdigest()


def test_hash_text_is_deterministic() -> None:
    assert hash_text("same") == hash_text("same")


def test_preview_text_truncates_to_200() -> None:
    assert preview_text("a" * 300) == "a" * 200


def test_preview_text_preserves_short_input() -> None:
    assert preview_text("short") == "short"


@pytest.mark.asyncio
async def test_save_scan_writes_row(db_session: AsyncSession) -> None:
    await save_scan(db_session, "hello world", _response())

    rows = (await db_session.execute(select(ScanRecord))).scalars().all()

    assert len(rows) == 1
    record = rows[0]
    assert record.text_hash == hash_text("hello world")
    assert record.text_preview == "hello world"
    assert record.source == "tool_output"
    assert record.severity == "HIGH"
    assert record.risk == 0.78
    assert record.blocking is True
    assert record.signals["density_risk"] == 0.62
    assert record.signals["matches"] == ["density=0.62"]
    assert record.created_at is not None


@pytest.mark.asyncio
async def test_record_to_response_extracts_json_fields(
    db_session: AsyncSession,
) -> None:
    record = await save_scan(db_session, "convert me", _response())

    response = record_to_response(record)

    assert response.severity is Severity.HIGH
    assert response.text_preview == "convert me"
    assert response.matches == ["density=0.62"]
    assert response.hotspots == [(10, 25)]
    assert response.signals.density_risk == 0.62
    assert response.created_at == record.created_at


@pytest.mark.asyncio
async def test_save_scan_persists_match_when_present(
    db_session: AsyncSession,
) -> None:
    pattern = AttackPattern(
        id=uuid.uuid4(),
        name="test-pattern",
        text="pattern text",
        source_corpus="test",
        category="test",
        embedding=[1.0] + [0.0] * 383,
    )
    db_session.add(pattern)
    await db_session.flush()

    response = _response().model_copy(
        update={
            "nearest_match": NearestMatch(
                id=pattern.id,
                name=pattern.name,
                source_corpus=pattern.source_corpus,
                category=pattern.category,
                distance=0.12,
            )
        }
    )

    record = await save_scan(db_session, "some text", response)

    assert record.matched_pattern_id == pattern.id
    assert record.match_distance == 0.12


@pytest.mark.asyncio
async def test_save_scan_persists_null_match_when_absent(
    db_session: AsyncSession,
) -> None:
    record = await save_scan(db_session, "some text", _response())

    assert record.matched_pattern_id is None
    assert record.match_distance is None


async def _seed(
    db_session: AsyncSession, count: int, severity: Severity = Severity.HIGH
) -> None:
    """Write `count` scan records with sequential previews."""
    for i in range(count):
        await save_scan(db_session, f"text {i}", _response(severity=severity))


@pytest.mark.asyncio
async def test_list_scans_empty(db_client: AsyncClient) -> None:
    response = await db_client.get("/scans")

    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0, "limit": 20, "offset": 0}


@pytest.mark.asyncio
async def test_list_scans_returns_items(
    db_client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, 3)

    response = await db_client.get("/scans")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["limit"] == 20
    assert body["offset"] == 0


@pytest.mark.asyncio
async def test_list_scans_pagination(
    db_client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, 5)

    response = await db_client.get("/scans", params={"limit": 2, "offset": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 2


@pytest.mark.asyncio
async def test_list_scans_filters_by_severity(
    db_client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, 2, severity=Severity.HIGH)
    await _seed(db_session, 3, severity=Severity.CLEAN)

    response = await db_client.get("/scans", params={"severity": "HIGH"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert all(i["severity"] == "HIGH" for i in body["items"])


@pytest.mark.asyncio
async def test_list_scans_filters_by_source(
    db_client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed(db_session, 2)

    response = await db_client.get(
        "/scans", params={"source": "retrieved_doc"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_scans_rejects_bad_limit(db_client: AsyncClient) -> None:
    response = await db_client.get("/scans", params={"limit": 101})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_scan_returns_record(
    db_client: AsyncClient, db_session: AsyncSession
) -> None:
    record = await save_scan(db_session, "fetch me", _response())

    response = await db_client.get(f"/scans/{record.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(record.id)
    assert body["text_preview"] == "fetch me"
    assert body["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_get_scan_missing_returns_404(db_client: AsyncClient) -> None:
    response = await db_client.get(
        "/scans/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scan_invalid_uuid_returns_422(
    db_client: AsyncClient,
) -> None:
    response = await db_client.get("/scans/not-a-uuid")

    assert response.status_code == 422
