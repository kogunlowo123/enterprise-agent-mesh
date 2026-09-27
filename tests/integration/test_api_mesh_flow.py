"""Integration tests for the full API mesh flow."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes.v1.mesh import _ENDPOINT_REGISTRY
from api.schemas.mesh import CircuitState


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    for node in _ENDPOINT_REGISTRY.values():
        node["healthy"] = True
        node["circuit_state"] = CircuitState.CLOSED
        node["failure_count"] = 0
    yield  # type: ignore[misc]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestFullMeshFlow:
    """Integration tests for complete mesh flows."""

    def test_route_then_check_health(self, client: TestClient) -> None:
        """Route a request, then verify health reflects correct state."""
        route_resp = client.post(
            "/api/v1/mesh/route",
            json={"agent_id": "integration-agent", "target_service": "agent-runtime"},
        )
        assert route_resp.status_code == 200

        health_resp = client.get("/api/v1/mesh/health")
        assert health_resp.status_code == 200
        health = health_resp.json()
        assert health["healthy_count"] > 0

    def test_break_circuit_affects_routing(self, client: TestClient) -> None:
        """Breaking a circuit should exclude that node from routing."""
        node_id = list(_ENDPOINT_REGISTRY.keys())[0]

        # Break the circuit
        break_resp = client.post(
            "/api/v1/circuit/break",
            json={"node_id": node_id, "action": "open", "reason": "test"},
        )
        assert break_resp.status_code == 200
        assert break_resp.json()["new_state"] == CircuitState.OPEN

        # Route request — should not select the open circuit node
        for _ in range(20):
            route_resp = client.post(
                "/api/v1/mesh/route",
                json={"agent_id": "test-agent", "target_service": "agent-runtime"},
            )
            assert route_resp.status_code == 200
            assert route_resp.json()["node_id"] != node_id

    def test_reset_circuit_restores_routing(self, client: TestClient) -> None:
        """Resetting an open circuit should allow routing to it again."""
        nodes = list(_ENDPOINT_REGISTRY.keys())

        # Open two circuits
        for nid in nodes[:2]:
            client.post(
                "/api/v1/circuit/break",
                json={"node_id": nid, "action": "open"},
            )

        # Should route to only the 3rd node
        route_resp = client.post(
            "/api/v1/mesh/route",
            json={"agent_id": "test-agent", "target_service": "agent-runtime"},
        )
        assert route_resp.status_code == 200
        assert route_resp.json()["node_id"] == nodes[2]

        # Reset all circuits
        reset_resp = client.post(
            "/api/v1/circuit/break",
            json={"node_id": "ALL", "action": "reset_all"},
        )
        assert reset_resp.status_code == 200

        # Now all 3 nodes should be available
        selected: set[str] = set()
        for _ in range(50):
            r = client.post(
                "/api/v1/mesh/route",
                json={"agent_id": "test-agent", "target_service": "agent-runtime"},
            )
            assert r.status_code == 200
            selected.add(r.json()["node_id"])

        assert len(selected) == 3

    def test_health_and_topology_consistency(self, client: TestClient) -> None:
        """Health and topology endpoints should report consistent node counts."""
        health = client.get("/api/v1/mesh/health").json()
        topology = client.get("/api/v1/mesh/topology").json()

        assert health["total_count"] == topology["total_nodes"]

    def test_service_health_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_readiness_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/v1/readiness")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
