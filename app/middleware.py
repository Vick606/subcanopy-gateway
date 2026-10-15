# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Victor
#
# This file is part of subcanopy-gateway. See LICENSE and
# COMMERCIAL_LICENSE.md at the repository root.

"""Rate limiting middleware.

Sliding window, in-memory. Per API key (hashed) when the header is
present, per client IP otherwise. Fails open: if the limiter itself
raises, the request is allowed. Blocking traffic because of a limiter
bug is worse than a brief rate limit bypass.

slowapi is not used. FastAPI 0.137 changed include_router so that
app.routes no longer contains included routes, and slowapi silently
skips them. A custom middleware wraps the ASGI app directly and does
not depend on route introspection.
"""

import hashlib
import hmac
import threading
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

EXEMPT_PATHS = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})


class SlidingWindowLimiter:
    """Thread-safe sliding window counter per key."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int, float]:
        """Return (allowed, remaining, reset_after_seconds)."""
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            timestamps = self._hits[key]
            timestamps[:] = [t for t in timestamps if t > cutoff]
            count = len(timestamps)
            if count >= self._limit:
                oldest = timestamps[0]
                reset_after = oldest + self._window - now
                return False, 0, max(reset_after, 0.0)
            timestamps.append(now)
            remaining = self._limit - count - 1
            return True, remaining, self._window


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        limit: int,
        pepper: bytes,
        window_seconds: float = 60.0,
    ) -> None:
        super().__init__(app)
        self._limit = limit
        self._window = window_seconds
        self._pepper = pepper
        self._limiter = SlidingWindowLimiter(limit, window_seconds)

    def _key(self, request: Request) -> str:
        raw_key = request.headers.get("X-API-Key")
        if raw_key:
            return hmac.new(
                self._pepper, raw_key.encode(), hashlib.sha256
            ).hexdigest()
        client = request.client
        return f"ip:{client.host}" if client else "unknown"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        try:
            allowed, remaining, reset_after = self._limiter.check(
                self._key(request)
            )
        except Exception:
            return await call_next(request)

        headers = {
            "X-RateLimit-Limit": str(self._limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_after)),
        }

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={**headers, "Retry-After": str(int(reset_after))},
            )

        response = await call_next(request)
        for name, value in headers.items():
            response.headers[name] = value
        return response
