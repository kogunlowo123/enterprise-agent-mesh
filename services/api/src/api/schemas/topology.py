"""Mesh topology schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TopologyNode(BaseModel):
    node_id: str
    service_name: str
    endpoint_url: str
    cloud_provider: str
    region: str
    healthy: bool
    circuit_state: str
    connections: list[str] = Field(default_factory=list)


class TopologyEdge(BaseModel):
    source: str
    target: str
    weight: float
    latency_ms: float | None = None
    active: bool = True


class TopologyGraph(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    generated_at: float
    total_nodes: int
    active_edges: int
