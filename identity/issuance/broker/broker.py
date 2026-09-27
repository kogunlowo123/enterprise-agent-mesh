"""JWT token broker for agent identity issuance."""

from __future__ import annotations

import time
from typing import Any

import jwt


class TokenBroker:
    """Issues short-lived JWT tokens for agent authentication."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        self._secret = secret_key
        self._algorithm = algorithm

    def issue(
        self,
        agent_id: str,
        scopes: list[str],
        tier: str = "T1",
        ttl_seconds: int = 3600,
    ) -> str:
        now = int(time.time())
        payload: dict[str, Any] = {
            "sub": agent_id,
            "iat": now,
            "exp": now + ttl_seconds,
            "scopes": scopes,
            "tier": tier,
            "type": "agent",
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify(self, token: str, required_scope: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = jwt.decode(
            token, self._secret, algorithms=[self._algorithm]
        )
        if required_scope and required_scope not in payload.get("scopes", []):
            raise PermissionError(f"Missing required scope: {required_scope}")
        return payload

    def refresh(self, token: str, ttl_seconds: int = 3600) -> str:
        payload = self.verify(token)
        return self.issue(
            agent_id=payload["sub"],
            scopes=payload.get("scopes", []),
            tier=payload.get("tier", "T1"),
            ttl_seconds=ttl_seconds,
        )
