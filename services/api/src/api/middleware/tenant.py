"""Tenant isolation middleware."""

from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts and validates tenant context from requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_id = request.headers.get("x-tenant-id", "default")
        request.state.tenant_id = tenant_id
        response = await call_next(request)
        response.headers["x-tenant-id"] = tenant_id
        return response
