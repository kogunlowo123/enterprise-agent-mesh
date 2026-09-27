"""Circuit breaker control endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, status

from api.routes.v1.mesh import _ENDPOINT_REGISTRY
from api.schemas.circuit import CircuitAction, CircuitBreakRequest, CircuitBreakResponse
from api.schemas.mesh import CircuitState

router = APIRouter(tags=["circuit"])


@router.post("/break", response_model=CircuitBreakResponse)
async def circuit_break(request: CircuitBreakRequest) -> CircuitBreakResponse:
    """Open, close, or reset a circuit breaker for a mesh node."""
    if request.action == CircuitAction.RESET_ALL:
        count = 0
        for node in _ENDPOINT_REGISTRY.values():
            if node["circuit_state"] != CircuitState.CLOSED:
                node["circuit_state"] = CircuitState.CLOSED
                node["failure_count"] = 0
                node["healthy"] = True
                count += 1
        return CircuitBreakResponse(
            node_id="ALL",
            previous_state="MIXED",
            new_state=CircuitState.CLOSED,
            action_taken=f"reset {count} circuits",
            timestamp=time.time(),
        )

    node = _ENDPOINT_REGISTRY.get(request.node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{request.node_id}' not found in registry",
        )

    previous_state = node["circuit_state"]

    if request.action == CircuitAction.OPEN:
        node["circuit_state"] = CircuitState.OPEN
        node["healthy"] = False
        new_state = CircuitState.OPEN
        action_taken = f"opened circuit: {request.reason}"

    elif request.action == CircuitAction.CLOSE:
        node["circuit_state"] = CircuitState.CLOSED
        node["failure_count"] = 0
        node["healthy"] = True
        new_state = CircuitState.CLOSED
        action_taken = "closed circuit"

    elif request.action == CircuitAction.RESET:
        node["circuit_state"] = CircuitState.CLOSED
        node["failure_count"] = 0
        node["healthy"] = True
        new_state = CircuitState.CLOSED
        action_taken = "reset circuit"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {request.action}",
        )

    return CircuitBreakResponse(
        node_id=request.node_id,
        previous_state=previous_state,
        new_state=new_state,
        action_taken=action_taken,
        timestamp=time.time(),
    )
