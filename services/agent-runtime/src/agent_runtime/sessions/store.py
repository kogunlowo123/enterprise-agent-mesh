"""Session store for agent sessions."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    tenant_id: str = ""
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    turns: int = 0
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """In-memory session store (production: use Redis)."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._sessions: dict[str, AgentSession] = {}
        self._ttl = ttl_seconds

    def create(self, agent_id: str, tenant_id: str) -> AgentSession:
        session = AgentSession(agent_id=agent_id, tenant_id=tenant_id)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> AgentSession | None:
        session = self._sessions.get(session_id)
        if session and (time.time() - session.last_active) > self._ttl:
            del self._sessions[session_id]
            return None
        return session

    def update(self, session_id: str, **kwargs: Any) -> None:
        session = self._sessions.get(session_id)
        if session:
            for k, v in kwargs.items():
                setattr(session, k, v)
            session.last_active = time.time()

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
