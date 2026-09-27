"""Unit tests for load balancing logic."""

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


class TestLoadBalancing:
    """Test load balancing weight distribution."""

    def test_all_nodes_can_be_selected(self, client: TestClient) -> None:
        """Under random selection, all nodes should eventually be selected."""
        selected_nodes: set[str] = set()

        for _ in range(100):
            response = client.post(
                "/api/v1/mesh/route",
                json={"agent_id": "lb-test", "target_service": "svc"},
            )
            assert response.status_code == 200
            selected_nodes.add(response.json()["node_id"])

        # With 3 nodes and 100 requests, all should be selected
        assert len(selected_nodes) == 3

    def test_topology_returns_all_nodes(self, client: TestClient) -> None:
        response = client.get("/api/v1/mesh/topology")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodes"] == 3

    def test_topology_edges_are_fully_connected(self, client: TestClient) -> None:
        response = client.get("/api/v1/mesh/topology")
        data = response.json()
        # 3 nodes fully connected = 3 edges
        assert len(data["edges"]) == 3

    def test_topology_active_edges_decrease_when_node_unhealthy(
        self, client: TestClient
    ) -> None:
        node_id = list(_ENDPOINT_REGISTRY.keys())[0]
        _ENDPOINT_REGISTRY[node_id]["healthy"] = False

        response = client.get("/api/v1/mesh/topology")
        data = response.json()
        # Edges involving unhealthy node should be inactive
        assert data["active_edges"] < 3

    def test_weight_distribution_sum(self, client: TestClient) -> None:
        total_weight = sum(
            node["weight"] for node in _ENDPOINT_REGISTRY.values()
        )
        assert abs(total_weight - 100.0) < 1.0  # Weights sum to ~100
