# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import hashlib

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import ScanRecord
from app.schemas import ScanResponse, Severity, SignalBreakdown
from app.services.history import hash_text, preview_text, save_scan


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
