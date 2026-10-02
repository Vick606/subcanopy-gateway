# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import ScanRecord
from app.schemas import ScanResponse

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
    )
    session.add(record)
    await session.commit()
    return record
