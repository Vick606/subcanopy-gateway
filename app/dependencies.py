# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

from functools import lru_cache

from subcanopy_guard import ContextScanner

from app.services.scanner import ScannerService


@lru_cache(maxsize=1)
def get_scanner_service() -> ScannerService:
    return ScannerService(ContextScanner())
