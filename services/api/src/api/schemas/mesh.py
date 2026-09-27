"""Mesh routing schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentTier(str, Enum):
    T0 = "T0"
    T1 = "T1"
    T2 = "T2"


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class RouteRequest(BaseModel):
    agent_id: str = Field(..., description="Requesting agent ID")
    target_service: str = Field(..., description="Target service name")
    payload_size: int = Field(default=0, description="Payload size in bytes")
    tier: AgentTier = Field(default=AgentTier.T1, description="Agent tier")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteDecision(BaseModel):
    endpoint_url: str = Field(..., description="Selected endpoint URL")
    latency_estimate_ms: float = Field(..., description="Estimated latency in ms")
    circuit_state: CircuitState = Field(..., description="Circuit breaker state")
    weight: float = Field(..., description="Load balancer weight used")
    node_id: str = Field(..., description="Selected node ID")


class MeshNodeHealth(BaseModel):
    node_id: str
    endpoint_url: str
    healthy: bool
    circuit_state: CircuitState
    failure_count: int
    last_success_at: float | None = None
    latency_p99_ms: float | None = None


class MeshHealthResponse(BaseModel):
    nodes: list[MeshNodeHealth]
    healthy_count: int
    total_count: int
    mesh_state: str
