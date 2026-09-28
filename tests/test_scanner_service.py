# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from collections.abc import Callable

import pytest
from subcanopy_guard import ScanResult

from app.schemas import Severity
from app.services.scanner import ScannerService, to_response


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


class _MappingScanner:
    """Stub scanner that derives a result from the input text."""

    def __init__(self, mapper: Callable[[str], ScanResult]) -> None:
        self._mapper = mapper
        self.calls: list[tuple[str, str | None]] = []

    def scan(self, text: str, source: str | None = None) -> ScanResult:
        self.calls.append((text, source))
        return self._mapper(text)


def test_scan_batch_returns_results_in_input_order() -> None:
    severities = {"a": "CLEAN", "b": "HIGH", "c": "LOW"}

    def mapper(text: str) -> ScanResult:
        return _result(severity=severities[text], risk=0.5)

    service = ScannerService(_MappingScanner(mapper))  # type: ignore[arg-type]
    batch = service.scan_batch(["a", "b", "c"])

    assert batch.count == 3
    assert [r.severity.value for r in batch.results] == ["CLEAN", "HIGH", "LOW"]
    assert [r.risk for r in batch.results] == [0.5, 0.5, 0.5]


def test_scan_batch_passes_source_to_each_item() -> None:
    stub = _MappingScanner(lambda _: _result())
    service = ScannerService(stub)  # type: ignore[arg-type]

    service.scan_batch(["a", "b"], source="tool_output")

    assert stub.calls == [("a", "tool_output"), ("b", "tool_output")]


def test_scan_batch_empty_list_returns_empty_response() -> None:
    service = ScannerService(_MappingScanner(lambda _: _result()))  # type: ignore[arg-type]

    batch = service.scan_batch([])

    assert batch.count == 0
    assert batch.results == []
