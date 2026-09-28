# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator
from subcanopy_guard.provenance import known_sources


class Severity(StrEnum):
    CLEAN = "CLEAN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ScanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)
    source: str | None = None

    @field_validator("source")
    @classmethod
    def _validate_source(cls, value: str | None) -> str | None:
        if value is None:
            return None
        allowed = known_sources()
        if value not in allowed:
            raise ValueError(f"source must be one of {allowed}")
        return value


class SignalBreakdown(BaseModel):
    density_risk: float
    discontinuity_risk: float
    provenance_multiplier: float


class ScanResponse(BaseModel):
    severity: Severity
    risk: float
    source: str
    blocking: bool
    matches: list[str]
    hotspots: list[tuple[int, int]]
    signals: SignalBreakdown
