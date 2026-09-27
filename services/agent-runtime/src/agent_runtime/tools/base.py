"""Base tool interface for agent tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base for all agent tools."""

    name: str
    description: str
    required_scope: str

    @abstractmethod
    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with given parameters."""
        ...

    def validate_scope(self, token_scopes: list[str]) -> bool:
        return self.required_scope in token_scopes
