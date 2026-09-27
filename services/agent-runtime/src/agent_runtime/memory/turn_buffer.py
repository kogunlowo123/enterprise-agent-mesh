"""In-memory turn buffer for agent conversation history."""

from __future__ import annotations

from collections import deque
from typing import Any


class TurnBuffer:
    """Fixed-size ring buffer for agent conversation turns."""

    def __init__(self, max_turns: int = 20) -> None:
        self._buffer: deque[dict[str, Any]] = deque(maxlen=max_turns)
        self._max_turns = max_turns

    def add(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        self._buffer.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
        })

    def get_messages(self) -> list[dict[str, Any]]:
        return list(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)
