# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

"""add match columns to scan_records

Revision ID: a3e3cba5e2c8
Revises: d2ef89d7c5af
Create Date: 2026-10-06 19:47:01.607577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'a3e3cba5e2c8'
down_revision: Union[str, Sequence[str], None] = 'd2ef89d7c5af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NAME = "fk_scan_records_matched_pattern_id_attack_patterns"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "scan_records",
        sa.Column("matched_pattern_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "scan_records",
        sa.Column("match_distance", sa.Float(), nullable=True),
    )
    op.create_index(
        op.f("ix_scan_records_matched_pattern_id"),
        "scan_records",
        ["matched_pattern_id"],
        unique=False,
    )
    op.create_foreign_key(
        FK_NAME,
        "scan_records",
        "attack_patterns",
        ["matched_pattern_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(FK_NAME, "scan_records", type_="foreignkey")
    op.drop_index(
        op.f("ix_scan_records_matched_pattern_id"),
        table_name="scan_records",
    )
    op.drop_column("scan_records", "match_distance")
    op.drop_column("scan_records", "matched_pattern_id")
