# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import pytest
from subcanopy_guard import ScanResult

from app.schemas import Severity
from app.services.scanner import to_response


def _result(severity: str = "HIGH", risk: float = 0.8) -> ScanResult:
    return ScanResult(
        severity=severity,
        risk=risk,
        source="tool_output",
        density_risk=0.62,
        discontinuity_risk=0.15,
        provenance_multiplier=1.35,
        matches=["density=0.62"],
        hotspots=[(10, 25)],
    )


def test_to_response_maps_all_fields() -> None:
    response = to_response(_result())

    assert response.severity is Severity.HIGH
    assert response.risk == 0.8
    assert response.source == "tool_output"
    assert response.blocking is True
    assert response.matches == ["density=0.62"]
    assert response.hotspots == [(10, 25)]
    assert response.signals.density_risk == 0.62
    assert response.signals.discontinuity_risk == 0.15
    assert response.signals.provenance_multiplier == 1.35


def test_to_response_low_severity_is_not_blocking() -> None:
    response = to_response(_result(severity="LOW", risk=0.2))

    assert response.severity is Severity.LOW
    assert response.blocking is False


def test_to_response_rejects_unknown_severity() -> None:
    with pytest.raises(ValueError):
        to_response(_result(severity="BOGUS"))
