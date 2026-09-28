# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from subcanopy_guard import ScanResult

from app.dependencies import get_scanner_service
from app.schemas import ScanResponse
from app.services.scanner import ScannerService


class _StubScanner:
    def __init__(self, result: ScanResult) -> None:
        self._result = result
        self.calls: list[tuple[str, str | None]] = []

    def scan(self, text: str, source: str | None = None) -> ScanResult:
        self.calls.append((text, source))
        return self._result


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


@pytest.fixture
def stub_scanner() -> _StubScanner:
    return _StubScanner(_result())


@pytest.fixture
def override_scanner(
    app: FastAPI, stub_scanner: _StubScanner
) -> Iterator[_StubScanner]:
    app.dependency_overrides[get_scanner_service] = lambda: ScannerService(
        stub_scanner  # type: ignore[arg-type]
    )
    yield stub_scanner
    app.dependency_overrides.clear()


def test_scan_returns_200_with_result(
    client: TestClient, override_scanner: _StubScanner
) -> None:
    response = client.post("/scan", json={"text": "hello"})

    assert response.status_code == 200
    body = ScanResponse.model_validate(response.json())
    assert body.severity.value == "HIGH"
    assert body.blocking is True
    assert body.hotspots == [(10, 25)]


def test_scan_passes_text_and_source_to_scanner(
    client: TestClient, override_scanner: _StubScanner
) -> None:
    client.post("/scan", json={"text": "hello", "source": "tool_output"})

    assert override_scanner.calls == [("hello", "tool_output")]


def test_scan_omitted_source_passes_none(
    client: TestClient, override_scanner: _StubScanner
) -> None:
    client.post("/scan", json={"text": "hello"})

    assert override_scanner.calls == [("hello", None)]


def test_scan_empty_text_returns_422(client: TestClient) -> None:
    response = client.post("/scan", json={"text": ""})

    assert response.status_code == 422


def test_scan_oversized_text_returns_422(client: TestClient) -> None:
    response = client.post("/scan", json={"text": "a" * 100_001})

    assert response.status_code == 422


def test_scan_unknown_source_returns_422(client: TestClient) -> None:
    response = client.post("/scan", json={"text": "hello", "source": "bogus"})

    assert response.status_code == 422


def test_scan_critical_severity_still_returns_200(
    client: TestClient, app: FastAPI
) -> None:
    app.dependency_overrides[get_scanner_service] = lambda: ScannerService(
        _StubScanner(_result(severity="CRITICAL", risk=0.95))  # type: ignore[arg-type]
    )

    response = client.post("/scan", json={"text": "hello"})

    assert response.status_code == 200
    assert response.json()["severity"] == "CRITICAL"
    assert response.json()["blocking"] is True
