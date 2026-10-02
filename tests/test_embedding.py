# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import numpy as np
import pytest

from app.services.embedding import EmbeddingService


class _FakeModel:
    """Stands in for SentenceTransformer. Returns a fixed vector."""

    def __init__(self, dim: int = 1024) -> None:
        self._dim = dim
        self.calls: list[tuple[str, bool]] = []

    def encode(
        self, text: str, normalize_embeddings: bool = False
    ) -> np.ndarray:
        self.calls.append((text, normalize_embeddings))
        return np.full(self._dim, 0.5, dtype=np.float32)


@pytest.mark.asyncio
async def test_embed_returns_list_of_floats() -> None:
    service = EmbeddingService(_FakeModel())  # type: ignore[arg-type]

    vector = await service.embed("hello")

    assert isinstance(vector, list)
    assert len(vector) == 1024
    assert all(isinstance(v, float) for v in vector)


@pytest.mark.asyncio
async def test_embed_requests_normalized_output() -> None:
    fake = _FakeModel()
    service = EmbeddingService(fake)  # type: ignore[arg-type]

    await service.embed("hello")

    assert fake.calls == [("hello", True)]


@pytest.mark.asyncio
async def test_embed_passes_text_through_unchanged() -> None:
    fake = _FakeModel()
    service = EmbeddingService(fake)  # type: ignore[arg-type]

    await service.embed("specific payload text")

    assert fake.calls[0][0] == "specific payload text"
