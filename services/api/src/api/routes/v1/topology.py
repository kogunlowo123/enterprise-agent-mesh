"""Mesh topology endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter

from api.routes.v1.mesh import _ENDPOINT_REGISTRY
from api.schemas.topology import TopologyEdge, TopologyGraph, TopologyNode

router = APIRouter(tags=["topology"])


@router.get("/topology", response_model=TopologyGraph)
async def get_topology() -> TopologyGraph:
    """Get live mesh topology graph."""
    nodes = []
    for node_id, node in _ENDPOINT_REGISTRY.items():
        cloud = node.get("cloud", "unknown")
        region_map = {"aws": "us-east-1", "azure": "eastus", "gcp": "us-central1"}
        nodes.append(
            TopologyNode(
                node_id=node_id,
                service_name="agent-runtime",
                endpoint_url=node["endpoint_url"],
                cloud_provider=cloud,
                region=region_map.get(cloud, "unknown"),
                healthy=node["healthy"],
                circuit_state=node["circuit_state"],
                connections=[
                    nid for nid in _ENDPOINT_REGISTRY if nid != node_id
                ],
            )
        )

    # Build mesh edges (fully connected topology)
    edges = []
    node_ids = list(_ENDPOINT_REGISTRY.keys())
    for i, src in enumerate(node_ids):
        for dst in node_ids[i + 1 :]:
            src_node = _ENDPOINT_REGISTRY[src]
            dst_node = _ENDPOINT_REGISTRY[dst]
            active = src_node["healthy"] and dst_node["healthy"]
            src_lat = src_node.get("latency_p99_ms", 50.0)
            dst_lat = dst_node.get("latency_p99_ms", 50.0)
            edges.append(
                TopologyEdge(
                    source=src,
                    target=dst,
                    weight=(src_node["weight"] + dst_node["weight"]) / 2,
                    latency_ms=(src_lat + dst_lat) / 2,
                    active=active,
                )
            )

    active_edges = sum(1 for e in edges if e.active)
    return TopologyGraph(
        nodes=nodes,
        edges=edges,
        generated_at=time.time(),
        total_nodes=len(nodes),
        active_edges=active_edges,
    )
