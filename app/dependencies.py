# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from functools import lru_cache

from fastapi import Request
from subcanopy_guard import ContextScanner

from app.config import Settings
from app.services.embedding import EmbeddingService
from app.services.scanner import ScannerService


@lru_cache(maxsize=1)
def get_scanner_service() -> ScannerService:
    return ScannerService(ContextScanner())


def get_embedding_service(request: Request) -> EmbeddingService:
    service: EmbeddingService | None = getattr(
        request.app.state, "embedding_service", None
    )
    if service is None:
        raise RuntimeError(
            "Embedding service is not initialized. "
            "The app must be created with with_embedding_model=True."
        )
    return service


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings
