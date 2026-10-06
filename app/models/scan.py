# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScanRecord(Base):
    __tablename__ = "scan_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    text_hash: Mapped[str] = mapped_column(String(64), index=True)
    text_preview: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    risk: Mapped[float] = mapped_column(Float)
    blocking: Mapped[bool] = mapped_column(default=False)
    signals: Mapped[dict] = mapped_column(JSONB)
    matched_pattern_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("attack_patterns.id", ondelete="SET NULL"),
        index=True,
    )
    match_distance: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
