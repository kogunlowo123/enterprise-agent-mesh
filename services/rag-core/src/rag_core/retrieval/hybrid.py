"""Hybrid retrieval combining dense and sparse search."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combines dense (vector) and sparse (BM25/keyword) retrieval."""

    def __init__(
        self,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        top_k: int = 10,
    ) -> None:
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        dense_results: list[dict[str, Any]],
        sparse_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge dense and sparse results using weighted scoring."""
        scores: dict[str, dict[str, Any]] = {}

        for i, result in enumerate(dense_results):
            doc_id = result["id"]
            rank_score = 1.0 / (i + 1)
            scores[doc_id] = {
                **result,
                "dense_score": result.get("score", 0.0),
                "rrf_score": self.dense_weight * rank_score,
            }

        for i, result in enumerate(sparse_results):
            doc_id = result["id"]
            rank_score = 1.0 / (i + 1)
            if doc_id in scores:
                scores[doc_id]["rrf_score"] += self.sparse_weight * rank_score
                scores[doc_id]["sparse_score"] = result.get("score", 0.0)
            else:
                scores[doc_id] = {
                    **result,
                    "sparse_score": result.get("score", 0.0),
                    "rrf_score": self.sparse_weight * rank_score,
                }

        merged = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
        return merged[: self.top_k]
