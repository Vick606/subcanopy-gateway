# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

"""resize embedding column to 384

Revision ID: d2ef89d7c5af
Revises: 9cfaa592e49d
Create Date: 2026-10-02 13:32:01.110133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'd2ef89d7c5af'
down_revision: Union[str, Sequence[str], None] = '9cfaa592e49d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(
        "ix_attack_patterns_embedding_hnsw", table_name="attack_patterns"
    )
    op.drop_column("attack_patterns", "embedding")
    op.add_column(
        "attack_patterns",
        sa.Column("embedding", Vector(dim=384), nullable=False),
    )
    op.create_index(
        "ix_attack_patterns_embedding_hnsw",
        "attack_patterns",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_attack_patterns_embedding_hnsw", table_name="attack_patterns"
    )
    op.drop_column("attack_patterns", "embedding")
    op.add_column(
        "attack_patterns",
        sa.Column("embedding", Vector(dim=1024), nullable=False),
    )
    op.create_index(
        "ix_attack_patterns_embedding_hnsw",
        "attack_patterns",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
