# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import ScanRecord
from app.schemas import (
    ScanRecordResponse,
    ScanResponse,
    Severity,
    SignalBreakdown,
)

PREVIEW_LENGTH = 200


def hash_text(text: str) -> str:
    """Return the SHA-256 hex digest of the text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def preview_text(text: str) -> str:
    """Return the first PREVIEW_LENGTH characters of the text."""
    return text[:PREVIEW_LENGTH]


async def save_scan(
    session: AsyncSession,
    text: str,
    response: ScanResponse,
) -> ScanRecord:
    """Persist a scan result and return the stored row."""
    match = response.nearest_match
    record = ScanRecord(
        text_hash=hash_text(text),
        text_preview=preview_text(text),
        source=response.source,
        severity=response.severity.value,
        risk=response.risk,
        blocking=response.blocking,
        signals={
            "density_risk": response.signals.density_risk,
            "discontinuity_risk": response.signals.discontinuity_risk,
            "provenance_multiplier": response.signals.provenance_multiplier,
            "matches": response.matches,
            "hotspots": response.hotspots,
        },
        matched_pattern_id=match.id if match else None,
        match_distance=match.distance if match else None,
    )
    session.add(record)
    await session.commit()
    return record


def record_to_response(record: ScanRecord) -> ScanRecordResponse:
    """Map a ScanRecord row to the API response shape."""
    signals = record.signals
    return ScanRecordResponse(
        id=record.id,
        text_hash=record.text_hash,
        text_preview=record.text_preview,
        source=record.source,
        severity=Severity(record.severity),
        risk=record.risk,
        blocking=record.blocking,
        matches=signals.get("matches", []),
        hotspots=signals.get("hotspots", []),
        signals=SignalBreakdown(
            density_risk=signals["density_risk"],
            discontinuity_risk=signals["discontinuity_risk"],
            provenance_multiplier=signals["provenance_multiplier"],
        ),
        matched_pattern_id=record.matched_pattern_id,
        match_distance=record.match_distance,
        created_at=record.created_at,
    )
