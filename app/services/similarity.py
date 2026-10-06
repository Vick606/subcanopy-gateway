# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attack import AttackPattern
from app.schemas import NearestMatch


async def find_nearest(
    session: AsyncSession,
    embedding: list[float],
    threshold: float,
) -> NearestMatch | None:
    """Return the closest attack pattern within the distance threshold.

    Distance is cosine distance: 0 is identical, 2 is opposite. Lower
    is more similar. Returns None if the table is empty or the closest
    pattern exceeds the threshold.
    """
    distance = AttackPattern.embedding.cosine_distance(embedding).label(
        "distance"
    )
    stmt = (
        select(AttackPattern, distance)
        .order_by(distance)
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None

    pattern, dist = row
    if dist > threshold:
        return None

    return NearestMatch(
        id=pattern.id,
        name=pattern.name,
        source_corpus=pattern.source_corpus,
        category=pattern.category,
        distance=float(dist),
    )
