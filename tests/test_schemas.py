# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import pytest
from pydantic import ValidationError

from app.schemas import (
    BatchScanRequest,
    BatchScanResponse,
    ScanRequest,
    ScanResponse,
    Severity,
    SignalBreakdown,
)


def test_scan_request_accepts_minimal_payload() -> None:
    request = ScanRequest(text="hello")

    assert request.text == "hello"
    assert request.source is None


def test_scan_request_rejects_empty_text() -> None:
    with pytest.raises(ValidationError):
        ScanRequest(text="")


def test_scan_request_rejects_oversized_text() -> None:
    with pytest.raises(ValidationError):
        ScanRequest(text="a" * 100_001)


def test_scan_request_accepts_known_source() -> None:
    request = ScanRequest(text="hello", source="tool_output")

    assert request.source == "tool_output"


def test_scan_request_rejects_unknown_source() -> None:
    with pytest.raises(ValidationError):
        ScanRequest(text="hello", source="not_a_real_source")


def test_scan_response_serializes_hotspots_as_arrays() -> None:
    response = ScanResponse(
        severity=Severity.HIGH,
        risk=0.8,
        source="tool_output",
        blocking=True,
        matches=["density=0.62"],
        hotspots=[(10, 25), (40, 60)],
        signals=SignalBreakdown(
            density_risk=0.62,
            discontinuity_risk=0.15,
            provenance_multiplier=1.35,
        ),
    )

    dumped = response.model_dump(mode="json")

    assert dumped["hotspots"] == [[10, 25], [40, 60]]
    assert dumped["severity"] == "HIGH"


def test_severity_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        Severity("UNKNOWN")


def test_batch_request_accepts_minimal_payload() -> None:
    request = BatchScanRequest(texts=["hello", "world"])

    assert request.texts == ["hello", "world"]
    assert request.source is None


def test_batch_request_rejects_empty_list() -> None:
    with pytest.raises(ValidationError):
        BatchScanRequest(texts=[])


def test_batch_request_rejects_more_than_100_items() -> None:
    with pytest.raises(ValidationError):
        BatchScanRequest(texts=["a"] * 101)


def test_batch_request_rejects_oversized_item() -> None:
    with pytest.raises(ValidationError):
        BatchScanRequest(texts=["ok", "a" * 100_001])


def test_batch_request_rejects_unknown_source() -> None:
    with pytest.raises(ValidationError):
        BatchScanRequest(texts=["hello"], source="bogus")


def test_batch_response_count_is_derived() -> None:
    response = BatchScanResponse(
        results=[
            ScanResponse(
                severity=Severity.CLEAN,
                risk=0.1,
                source="user_input",
                blocking=False,
                matches=[],
                hotspots=[],
                signals=SignalBreakdown(
                    density_risk=0.1,
                    discontinuity_risk=0.0,
                    provenance_multiplier=1.0,
                ),
            ),
            ScanResponse(
                severity=Severity.HIGH,
                risk=0.8,
                source="tool_output",
                blocking=True,
                matches=["density=0.62"],
                hotspots=[(10, 25)],
                signals=SignalBreakdown(
                    density_risk=0.62,
                    discontinuity_risk=0.15,
                    provenance_multiplier=1.35,
                ),
            ),
        ]
    )

    dumped = response.model_dump(mode="json")

    assert dumped["count"] == 2
    assert len(dumped["results"]) == 2
