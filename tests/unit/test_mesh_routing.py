"""Unit tests for mesh routing logic."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes.v1.mesh import _ENDPOINT_REGISTRY
from api.schemas.mesh import CircuitState


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    """Reset endpoint registry state before each test."""
    for node in _ENDPOINT_REGISTRY.values():
        node["healthy"] = True
        node["circuit_state"] = CircuitState.CLOSED
        node["failure_count"] = 0
    yield  # type: ignore[misc]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestMeshRoute:
    """Test POST /api/v1/mesh/route endpoint."""

    def test_route_returns_valid_decision(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/mesh/route",
            json={
                "agent_id": "test-agent",
                "target_service": "agent-runtime",
                "payload_size": 100,
                "tier": "T1",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "endpoint_url" in data
        assert "latency_estimate_ms" in data
        assert "circuit_state" in data
        assert "node_id" in data
        assert data["circuit_state"] == CircuitState.CLOSED

    def test_route_selects_healthy_endpoint(self, client: TestClient) -> None:
        # Mark two nodes as unhealthy
        nodes = list(_ENDPOINT_REGISTRY.keys())
        _ENDPOINT_REGISTRY[nodes[0]]["healthy"] = False
        _ENDPOINT_REGISTRY[nodes[1]]["healthy"] = False

        response = client.post(
            "/api/v1/mesh/route",
            json={"agent_id": "test-agent", "target_service": "agent-runtime"},
        )
        assert response.status_code == 200
        # Should route to the remaining healthy node
        assert response.json()["node_id"] == nodes[2]

    def test_route_503_when_all_unhealthy(self, client: TestClient) -> None:
        for node in _ENDPOINT_REGISTRY.values():
            node["healthy"] = False

        response = client.post(
            "/api/v1/mesh/route",
            json={"agent_id": "test-agent", "target_service": "agent-runtime"},
        )
        assert response.status_code == 503

    def test_route_skips_open_circuits(self, client: TestClient) -> None:
        nodes = list(_ENDPOINT_REGISTRY.keys())
        _ENDPOINT_REGISTRY[nodes[0]]["circuit_state"] = CircuitState.OPEN
        _ENDPOINT_REGISTRY[nodes[1]]["circuit_state"] = CircuitState.OPEN

        response = client.post(
            "/api/v1/mesh/route",
            json={"agent_id": "test-agent", "target_service": "agent-runtime"},
        )
        assert response.status_code == 200
        assert response.json()["node_id"] == nodes[2]

    def test_route_with_t0_tier(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/mesh/route",
            json={
                "agent_id": "critical-agent",
                "target_service": "agent-runtime",
                "tier": "T0",
            },
        )
        assert response.status_code == 200
        assert response.json()["circuit_state"] in [
            CircuitState.CLOSED,
            CircuitState.HALF_OPEN,
        ]

    def test_route_latency_increases_with_payload(self, client: TestClient) -> None:
        r1 = client.post(
            "/api/v1/mesh/route",
            json={"agent_id": "a1", "target_service": "svc", "payload_size": 0},
        )
        r2 = client.post(
            "/api/v1/mesh/route",
            json={"agent_id": "a2", "target_service": "svc", "payload_size": 100000},
        )
        assert r1.status_code == 200
        assert r2.status_code == 200


class TestMeshHealth:
    """Test GET /api/v1/mesh/health endpoint."""

    def test_health_returns_all_nodes(self, client: TestClient) -> None:
        response = client.get("/api/v1/mesh/health")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3
        assert data["healthy_count"] == 3
        assert data["mesh_state"] == "HEALTHY"

    def test_health_degraded_with_open_circuit(self, client: TestClient) -> None:
        node_id = list(_ENDPOINT_REGISTRY.keys())[0]
        _ENDPOINT_REGISTRY[node_id]["circuit_state"] = CircuitState.OPEN

        response = client.get("/api/v1/mesh/health")
        assert response.status_code == 200
        data = response.json()
        assert data["mesh_state"] == "DEGRADED"

    def test_health_critical_when_all_unhealthy(self, client: TestClient) -> None:
        for node in _ENDPOINT_REGISTRY.values():
            node["healthy"] = False

        response = client.get("/api/v1/mesh/health")
        assert response.status_code == 200
        data = response.json()
        assert data["mesh_state"] == "CRITICAL"
        assert data["healthy_count"] == 0
