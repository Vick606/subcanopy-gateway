# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from subcanopy_guard import ContextScanner, ScanResult

from app.schemas import ScanResponse, Severity, SignalBreakdown


class ScannerService:
    def __init__(self, scanner: ContextScanner) -> None:
        self._scanner = scanner

    def scan(self, text: str, source: str | None = None) -> ScanResponse:
        return to_response(self._scanner.scan(text, source=source))


def to_response(result: ScanResult) -> ScanResponse:
    return ScanResponse(
        severity=Severity(result.severity),
        risk=result.risk,
        source=result.source,
        blocking=result.is_blocking(),
        matches=result.matches,
        hotspots=result.hotspots,
        signals=SignalBreakdown(
            density_risk=result.density_risk,
            discontinuity_risk=result.discontinuity_risk,
            provenance_multiplier=result.provenance_multiplier,
        ),
    )
