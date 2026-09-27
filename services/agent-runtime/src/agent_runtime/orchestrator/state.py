"""Shared state definitions for agent orchestration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Base state for all agent graphs."""

    session_id: str
    agent_id: str
    tenant_id: str
    turn: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
