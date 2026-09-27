"""OpenTelemetry tracing middleware."""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TracingMiddleware(BaseHTTPMiddleware):
    """Adds trace IDs and request timing to all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
        start_time = time.monotonic()

        request.state.trace_id = trace_id

        response = await call_next(request)

        duration_ms = (time.monotonic() - start_time) * 1000
        response.headers["x-trace-id"] = trace_id
        response.headers["x-duration-ms"] = f"{duration_ms:.2f}"

        return response
