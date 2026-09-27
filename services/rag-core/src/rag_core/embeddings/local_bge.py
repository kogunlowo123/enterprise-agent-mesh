"""Local BGE embedding model using sentence-transformers."""

from __future__ import annotations

import logging
import os

from rag_core.embeddings.base import BaseEmbedder

logger = logging.getLogger(__name__)


class LocalBGEEmbedder(BaseEmbedder):
    """BGE embedding model using sentence-transformers (runs locally)."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ) -> None:
        self._model_name = model_name or os.environ.get(
            "EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5"
        )
        self._device = device or os.environ.get("EMBEDDING_DEVICE", "cpu")
        self._model = None

    def _load_model(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s on %s", self._model_name, self._device)
            self._model = SentenceTransformer(self._model_name, device=self._device)

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        assert self._model is not None
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        # BGE models benefit from instruction prefix for queries
        query_text = f"Represent this sentence for searching relevant passages: {text}"
        return self.embed([query_text])[0]

    @property
    def dimension(self) -> int:
        return 1024  # bge-large-en-v1.5 dimension
