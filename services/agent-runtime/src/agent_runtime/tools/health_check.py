"""Health check tool for mesh nodes."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx


class HealthCheckTool:
    """Checks health of mesh node endpoints."""

    name = "health_check"
    description = "Check health status of a mesh node endpoint"
    required_scope = "mesh:read_topology"

    def __init__(self, timeout: float = 5.0) -> None:
        self._timeout = timeout

    async def run(self, endpoint_url: str, node_id: str = "") -> dict[str, Any]:
        """Check health of a single endpoint."""
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{endpoint_url}/api/v1/health")
            latency_ms = (time.monotonic() - start) * 1000
            return {
                "node_id": node_id,
                "endpoint_url": endpoint_url,
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
            }
        except httpx.HTTPError as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return {
                "node_id": node_id,
                "endpoint_url": endpoint_url,
                "healthy": False,
                "status_code": None,
                "latency_ms": round(latency_ms, 2),
                "error": str(exc),
            }

    async def check_all(self, endpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Check health of multiple endpoints concurrently."""
        tasks = [
            self.run(ep["endpoint_url"], ep.get("node_id", ""))
            for ep in endpoints
        ]
        return await asyncio.gather(*tasks)
