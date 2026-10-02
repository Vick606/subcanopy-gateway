# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import asyncio

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model: SentenceTransformer) -> None:
        self._model = model

    async def embed(self, text: str) -> list[float]:
        """Encode text to a normalized embedding vector.

        Runs the synchronous encode call in a thread so the event loop
        is not blocked. normalize_embeddings=True is required for
        cosine distance to be meaningful.
        """
        vector = await asyncio.to_thread(
            self._model.encode,
            text,
            normalize_embeddings=True,
        )
        return vector.tolist()


def load_model(model_name: str) -> SentenceTransformer:
    """Load the model. Blocking. Call via asyncio.to_thread."""
    return SentenceTransformer(model_name)
