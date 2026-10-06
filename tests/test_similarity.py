# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack import AttackPattern
from app.services.similarity import find_nearest


async def _add_pattern(
    session: AsyncSession,
    name: str,
    embedding: list[float],
) -> AttackPattern:
    pattern = AttackPattern(
        id=uuid.uuid4(),
        name=name,
        text=f"text for {name}",
        source_corpus="test",
        category="test",
        embedding=embedding,
    )
    session.add(pattern)
    await session.commit()
    return pattern


@pytest.mark.asyncio
async def test_find_nearest_empty_table_returns_none(
    db_session: AsyncSession,
) -> None:
    match = await find_nearest(db_session, [0.1] * 384, threshold=0.5)

    assert match is None


@pytest.mark.asyncio
async def test_find_nearest_returns_closest_pattern(
    db_session: AsyncSession,
) -> None:
    await _add_pattern(db_session, "far", [1.0] + [0.0] * 383)
    await _add_pattern(db_session, "close", [0.0] * 383 + [1.0])

    match = await find_nearest(db_session, [0.0] * 383 + [1.0], threshold=0.5)

    assert match is not None
    assert match.name == "close"
    assert match.distance < 0.01


@pytest.mark.asyncio
async def test_find_nearest_above_threshold_returns_none(
    db_session: AsyncSession,
) -> None:
    await _add_pattern(db_session, "orthogonal", [1.0] + [0.0] * 383)

    match = await find_nearest(db_session, [0.0] * 383 + [1.0], threshold=0.5)

    assert match is None
