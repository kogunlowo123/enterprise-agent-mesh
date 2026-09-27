"""Mesh routing API endpoints."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.mesh import (
    CircuitState,
    MeshHealthResponse,
    MeshNodeHealth,
    RouteDecision,
    RouteRequest,
)

router = APIRouter(tags=["mesh"])

# In-memory endpoint registry (production: replace with Redis/DB-backed store)
_ENDPOINT_REGISTRY: dict[str, dict] = {
    "agent-runtime-aws": {
        "endpoint_url": "http://agent-runtime.aws.svc.cluster.local:8001",
        "cloud": "aws",
        "weight": 40.0,
        "healthy": True,
        "failure_count": 0,
        "circuit_state": CircuitState.CLOSED,
        "last_success_at": time.time(),
        "latency_p99_ms": 45.0,
    },
    "agent-runtime-azure": {
        "endpoint_url": "http://agent-runtime.azure.svc.cluster.local:8001",
        "cloud": "azure",
        "weight": 30.0,
        "healthy": True,
        "failure_count": 0,
        "circuit_state": CircuitState.CLOSED,
        "last_success_at": time.time(),
        "latency_p99_ms": 52.0,
    },
    "agent-runtime-gcp": {
        "endpoint_url": "http://agent-runtime.gcp.svc.cluster.local:8001",
        "cloud": "gcp",
        "weight": 30.0,
        "healthy": True,
        "failure_count": 0,
        "circuit_state": CircuitState.CLOSED,
        "last_success_at": time.time(),
        "latency_p99_ms": 48.0,
    },
}


def _select_endpoint(target_service: str, tier: str) -> tuple[str, dict]:
    """Select optimal endpoint using weighted round-robin with circuit state check."""
    import random

    available = [
        (node_id, node)
        for node_id, node in _ENDPOINT_REGISTRY.items()
        if node["healthy"] and node["circuit_state"] != CircuitState.OPEN
    ]

    if not available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No healthy endpoints available",
        )

    # Weighted selection
    total_weight = sum(node["weight"] for _, node in available)
    r = random.uniform(0, total_weight)
    cumulative = 0.0
    selected_id, selected_node = available[0]
    for node_id, node in available:
        cumulative += node["weight"]
        if r <= cumulative:
            selected_id, selected_node = node_id, node
            break

    return selected_id, selected_node


@router.post("/route", response_model=RouteDecision)
async def route_agent_request(request: RouteRequest) -> RouteDecision:
    """Route an agent request to the optimal mesh endpoint.

    Queries the endpoint registry, checks circuit breaker state,
    applies load balancing weights, and returns the routing decision.
    """
    node_id, node = _select_endpoint(request.target_service, request.tier)

    # Estimate latency based on tier and payload
    base_latency = node.get("latency_p99_ms", 50.0)
    payload_overhead = request.payload_size / 10000  # 0.1ms per KB
    estimated_latency = base_latency + payload_overhead

    return RouteDecision(
        endpoint_url=node["endpoint_url"],
        latency_estimate_ms=round(estimated_latency, 2),
        circuit_state=node["circuit_state"],
        weight=node["weight"],
        node_id=node_id,
    )


@router.get("/health", response_model=MeshHealthResponse)
async def mesh_health() -> MeshHealthResponse:
    """Get health status of all mesh nodes."""
    nodes = []
    for node_id, node in _ENDPOINT_REGISTRY.items():
        nodes.append(
            MeshNodeHealth(
                node_id=node_id,
                endpoint_url=node["endpoint_url"],
                healthy=node["healthy"],
                circuit_state=node["circuit_state"],
                failure_count=node["failure_count"],
                last_success_at=node.get("last_success_at"),
                latency_p99_ms=node.get("latency_p99_ms"),
            )
        )

    healthy_count = sum(1 for n in nodes if n.healthy)
    total_count = len(nodes)
    open_circuits = sum(1 for n in nodes if n.circuit_state == CircuitState.OPEN)

    if healthy_count == 0:
        mesh_state = "CRITICAL"
    elif open_circuits > 0:
        mesh_state = "DEGRADED"
    else:
        mesh_state = "HEALTHY"

    return MeshHealthResponse(
        nodes=nodes,
        healthy_count=healthy_count,
        total_count=total_count,
        mesh_state=mesh_state,
    )
