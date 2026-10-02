# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

"""Seed the attack_patterns table from data/attack_patterns.jsonl.

Usage:
    uv run python -m app.scripts.seed

Idempotent: ON CONFLICT (name) DO NOTHING means re-running after a
partial seed, or after adding new corpus entries, only inserts what is
missing.
"""

import asyncio
import json
import uuid
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy.dialects.postgresql import insert

from app.config import get_settings
from app.database import create_engine, create_session_factory
from app.models.attack import AttackPattern

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "attack_patterns.jsonl"
BATCH_SIZE = 32


def load_patterns(path: Path) -> list[dict]:
    """Read the JSONL corpus into a list of dicts."""
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


async def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    patterns = load_patterns(DATA_PATH)
    print(f"Loaded {len(patterns)} patterns from {DATA_PATH}")

    print(f"Loading model {settings.embedding_model}...")
    model = await asyncio.to_thread(
        SentenceTransformer, settings.embedding_model
    )

    texts = [p["text"] for p in patterns]
    print(f"Embedding {len(texts)} texts in batches of {BATCH_SIZE}...")
    embeddings = await asyncio.to_thread(
        model.encode,
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    rows = [
        {
            "id": uuid.uuid4(),
            "name": pattern["name"],
            "text": pattern["text"],
            "source_corpus": pattern["source_corpus"],
            "category": pattern["category"],
            "embedding": embedding.tolist(),
        }
        for pattern, embedding in zip(patterns, embeddings, strict=True)
    ]

    async with session_factory() as session:
        stmt = insert(AttackPattern).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
        stmt = stmt.returning(AttackPattern.name)
        result = await session.execute(stmt)
        inserted = len(result.fetchall())
        await session.commit()

    await engine.dispose()

    print(
        f"Inserted {inserted} new patterns "
        f"(skipped {len(rows) - inserted} existing)"
    )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
