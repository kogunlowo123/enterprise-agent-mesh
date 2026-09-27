"""LangGraph mesh-router agent graph."""

from __future__ import annotations

import logging
import time
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from agent_runtime.tools.circuit_control import CircuitState, registry

logger = logging.getLogger(__name__)


# --- State Definition ---

class MeshRouterState(TypedDict):
    """State for the mesh-router LangGraph agent."""

    route_request: dict[str, Any]
    available_endpoints: list[dict[str, Any]]
    circuit_states: dict[str, str]
    scored_endpoints: list[dict[str, Any]]
    selected_endpoint: dict[str, Any] | None
    routing_decision: dict[str, Any] | None
    error: str | None


# --- Agent Nodes ---

def discover_endpoints(state: MeshRouterState) -> MeshRouterState:
    """Discover available mesh endpoints from the registry."""
    # In production this would query a service registry (e.g., Consul, K8s API)
    endpoints = [
        {
            "node_id": "agent-runtime-aws",
            "endpoint_url": "http://agent-runtime.aws.svc.cluster.local:8001",
            "cloud": "aws",
            "weight": 40.0,
            "healthy": True,
            "latency_p99_ms": 45.0,
        },
        {
            "node_id": "agent-runtime-azure",
            "endpoint_url": "http://agent-runtime.azure.svc.cluster.local:8001",
            "cloud": "azure",
            "weight": 30.0,
            "healthy": True,
            "latency_p99_ms": 52.0,
        },
        {
            "node_id": "agent-runtime-gcp",
            "endpoint_url": "http://agent-runtime.gcp.svc.cluster.local:8001",
            "cloud": "gcp",
            "weight": 30.0,
            "healthy": True,
            "latency_p99_ms": 48.0,
        },
    ]

    logger.info("Discovered %d endpoints", len(endpoints))
    return {**state, "available_endpoints": endpoints}


def check_circuits(state: MeshRouterState) -> MeshRouterState:
    """Check circuit breaker state for all discovered endpoints."""
    circuit_states: dict[str, str] = {}

    for endpoint in state["available_endpoints"]:
        node_id = endpoint["node_id"]
        cb = registry.get_or_create(node_id)
        circuit_states[node_id] = cb.state.value

    logger.info("Circuit states: %s", circuit_states)
    return {**state, "circuit_states": circuit_states}


def score_endpoints(state: MeshRouterState) -> MeshRouterState:
    """Score endpoints based on circuit state, latency, and weight."""
    scored: list[dict[str, Any]] = []

    tier_multipliers = {"T0": 1.5, "T1": 1.0, "T2": 0.7}
    tier = state["route_request"].get("tier", "T1")
    tier_mult = tier_multipliers.get(tier, 1.0)

    for endpoint in state["available_endpoints"]:
        node_id = endpoint["node_id"]
        circuit_state = state["circuit_states"].get(node_id, CircuitState.OPEN.value)

        # Skip OPEN circuits
        if circuit_state == CircuitState.OPEN.value:
            logger.info("Skipping %s: circuit OPEN", node_id)
            continue

        # Skip unhealthy endpoints
        if not endpoint.get("healthy", False):
            logger.info("Skipping %s: unhealthy", node_id)
            continue

        latency = endpoint.get("latency_p99_ms", 100.0)
        weight = endpoint.get("weight", 1.0)

        # Score: higher weight + lower latency = better score
        # HALF_OPEN gets penalty
        circuit_penalty = 0.5 if circuit_state == CircuitState.HALF_OPEN.value else 1.0
        score = (weight / max(latency, 1.0)) * tier_mult * circuit_penalty

        scored.append({**endpoint, "score": score, "circuit_state": circuit_state})

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    logger.info("Scored %d endpoints", len(scored))
    return {**state, "scored_endpoints": scored}


def select_optimal(state: MeshRouterState) -> MeshRouterState:
    """Select the optimal endpoint from scored candidates."""
    scored = state["scored_endpoints"]

    if not scored:
        return {
            **state,
            "selected_endpoint": None,
            "error": "No available endpoints after circuit check",
        }

    # Use weighted probabilistic selection from top candidates (up to 3)
    import random

    candidates = scored[:3]
    total_score = sum(c["score"] for c in candidates)

    r = random.uniform(0, total_score)
    cumulative = 0.0
    selected = candidates[0]
    for candidate in candidates:
        cumulative += candidate["score"]
        if r <= cumulative:
            selected = candidate
            break

    logger.info("Selected endpoint: %s", selected["node_id"])
    return {**state, "selected_endpoint": selected, "error": None}


def emit_route_event(state: MeshRouterState) -> MeshRouterState:
    """Emit CloudEvent for the routing decision."""
    selected = state["selected_endpoint"]

    if selected is None:
        routing_decision = {
            "success": False,
            "error": state.get("error", "No endpoint selected"),
            "timestamp": time.time(),
        }
    else:
        payload_size = state["route_request"].get("payload_size", 0)
        base_latency = selected.get("latency_p99_ms", 50.0)
        latency_estimate = base_latency + payload_size / 10000

        routing_decision = {
            "success": True,
            "endpoint_url": selected["endpoint_url"],
            "node_id": selected["node_id"],
            "circuit_state": selected["circuit_state"],
            "weight": selected["weight"],
            "latency_estimate_ms": round(latency_estimate, 2),
            "timestamp": time.time(),
        }

        # Emit CloudEvent
        cloud_event = {
            "specversion": "1.0",
            "type": "mesh.routed",
            "source": "enterprise-agent-mesh/mesh-router",
            "id": f"route-{int(time.time() * 1000)}",
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": routing_decision,
        }
        logger.info("CloudEvent mesh.routed: node=%s", selected["node_id"])

    return {**state, "routing_decision": routing_decision}


def should_retry(state: MeshRouterState) -> Literal["retry", "complete"]:
    """Determine if routing should be retried."""
    if state.get("error") and not state.get("selected_endpoint"):
        return "complete"  # No endpoints available, fail fast
    return "complete"


# --- Graph Construction ---

def build_mesh_router_graph() -> StateGraph:
    """Build and compile the mesh-router LangGraph."""
    graph = StateGraph(MeshRouterState)

    graph.add_node("discover_endpoints", discover_endpoints)
    graph.add_node("check_circuits", check_circuits)
    graph.add_node("score_endpoints", score_endpoints)
    graph.add_node("select_optimal", select_optimal)
    graph.add_node("emit_route_event", emit_route_event)

    graph.set_entry_point("discover_endpoints")
    graph.add_edge("discover_endpoints", "check_circuits")
    graph.add_edge("check_circuits", "score_endpoints")
    graph.add_edge("score_endpoints", "select_optimal")
    graph.add_edge("select_optimal", "emit_route_event")
    graph.add_edge("emit_route_event", END)

    return graph


# Compiled graph instance
mesh_router_graph = build_mesh_router_graph().compile()


async def route_request(
    agent_id: str,
    target_service: str,
    payload_size: int = 0,
    tier: str = "T1",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute the mesh-router graph to route an agent request."""
    initial_state: MeshRouterState = {
        "route_request": {
            "agent_id": agent_id,
            "target_service": target_service,
            "payload_size": payload_size,
            "tier": tier,
            "metadata": metadata or {},
        },
        "available_endpoints": [],
        "circuit_states": {},
        "scored_endpoints": [],
        "selected_endpoint": None,
        "routing_decision": None,
        "error": None,
    }

    result = await mesh_router_graph.ainvoke(initial_state)
    return result.get("routing_decision", {"success": False, "error": "Graph execution failed"})
