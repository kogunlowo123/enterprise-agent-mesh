"""Base embedding interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query text."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        ...
