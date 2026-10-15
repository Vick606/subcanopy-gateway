# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

import time

from app.middleware import SlidingWindowLimiter


def test_sliding_window_allows_under_limit() -> None:
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60.0)

    for _ in range(3):
        allowed, remaining, _ = limiter.check("key-a")
        assert allowed is True

    allowed, remaining, _ = limiter.check("key-a")
    assert allowed is False
    assert remaining == 0


def test_sliding_window_isolates_keys() -> None:
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60.0)

    limiter.check("key-a")
    limiter.check("key-a")

    allowed, _, _ = limiter.check("key-b")
    assert allowed is True


def test_sliding_window_reports_remaining() -> None:
    limiter = SlidingWindowLimiter(limit=5, window_seconds=60.0)

    _, remaining, _ = limiter.check("key-a")
    assert remaining == 4

    _, remaining, _ = limiter.check("key-a")
    assert remaining == 3


def test_sliding_window_expires_old_hits() -> None:
    limiter = SlidingWindowLimiter(limit=2, window_seconds=0.1)

    limiter.check("key-a")
    limiter.check("key-a")
    allowed, _, _ = limiter.check("key-a")
    assert allowed is False

    time.sleep(0.15)

    allowed, _, _ = limiter.check("key-a")
    assert allowed is True


def test_sliding_window_returns_reset_time() -> None:
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60.0)

    limiter.check("key-a")
    allowed, _, reset_after = limiter.check("key-a")

    assert allowed is False
    assert 0.0 < reset_after <= 60.0
