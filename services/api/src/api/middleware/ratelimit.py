"""Rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiter per tenant."""

    def __init__(self, app: object, requests_per_minute: int = 1000) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._rpm = requests_per_minute
        self._buckets: dict[str, dict] = defaultdict(
            lambda: {"tokens": requests_per_minute, "last_refill": time.monotonic()}
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = getattr(request.state, "tenant_id", "default")
        bucket = self._buckets[tenant_id]

        now = time.monotonic()
        elapsed = now - bucket["last_refill"]
        refill = elapsed * (self._rpm / 60.0)
        bucket["tokens"] = min(self._rpm, bucket["tokens"] + refill)
        bucket["last_refill"] = now

        if bucket["tokens"] < 1:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "1"},
            )

        bucket["tokens"] -= 1
        return await call_next(request)
