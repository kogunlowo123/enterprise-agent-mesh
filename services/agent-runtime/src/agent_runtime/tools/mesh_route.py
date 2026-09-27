"""Mesh routing tool for agent-to-agent communication."""

from __future__ import annotations

from typing import Any

from agent_runtime.orchestrator.graph import route_request


class MeshRouteTool:
    """Routes requests through the mesh to target services."""

    name = "mesh_route"
    description = "Route a request through the agent mesh to a target service"
    required_scope = "mesh:route"

    async def run(
        self,
        agent_id: str,
        target_service: str,
        payload: dict[str, Any] | None = None,
        tier: str = "T1",
    ) -> dict[str, Any]:
        """Route a request to the optimal mesh endpoint."""
        payload_size = len(str(payload)) if payload else 0
        return await route_request(
            agent_id=agent_id,
            target_service=target_service,
            payload_size=payload_size,
            tier=tier,
        )
