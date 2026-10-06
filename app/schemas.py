# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, computed_field
from subcanopy_guard.provenance import known_sources


def _check_source(value: str) -> str:
    allowed = known_sources()
    if value not in allowed:
        raise ValueError(f"source must be one of {allowed}")
    return value


TextContent = Annotated[str, Field(min_length=1, max_length=100_000)]
SourceTag = Annotated[str, AfterValidator(_check_source)]


class Severity(StrEnum):
    CLEAN = "CLEAN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ScanRequest(BaseModel):
    text: TextContent
    source: SourceTag | None = None


class SignalBreakdown(BaseModel):
    density_risk: float
    discontinuity_risk: float
    provenance_multiplier: float


class NearestMatch(BaseModel):
    id: UUID
    name: str
    source_corpus: str
    category: str
    distance: float


class ScanResponse(BaseModel):
    severity: Severity
    risk: float
    source: str
    blocking: bool
    matches: list[str]
    hotspots: list[tuple[int, int]]
    signals: SignalBreakdown
    nearest_match: NearestMatch | None = None


class BatchScanRequest(BaseModel):
    texts: list[TextContent] = Field(min_length=1, max_length=100)
    source: SourceTag | None = None


class BatchScanResponse(BaseModel):
    results: list[ScanResponse]

    @computed_field
    @property
    def count(self) -> int:
        return len(self.results)


class ScanRecordResponse(BaseModel):
    id: UUID
    text_hash: str
    text_preview: str | None
    source: str
    severity: Severity
    risk: float
    blocking: bool
    matches: list[str]
    hotspots: list[tuple[int, int]]
    signals: SignalBreakdown
    created_at: datetime


class ScanListResponse(BaseModel):
    items: list[ScanRecordResponse]
    total: int
    limit: int
    offset: int
