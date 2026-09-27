"""Circuit breaker schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CircuitAction(str, Enum):
    OPEN = "open"
    CLOSE = "close"
    RESET = "reset"
    RESET_ALL = "reset_all"


class CircuitBreakRequest(BaseModel):
    node_id: str = Field(..., description="Mesh node ID to control")
    action: CircuitAction = Field(default=CircuitAction.OPEN)
    reason: str = Field(default="", description="Reason for circuit break")


class CircuitBreakResponse(BaseModel):
    node_id: str
    previous_state: str
    new_state: str
    action_taken: str
    timestamp: float
