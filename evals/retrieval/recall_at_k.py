"""Recall@K evaluation metric for retrieval."""

from __future__ import annotations


def recall_at_k(relevant_ids: set[str], retrieved_ids: list[str], k: int) -> float:
    """Compute Recall@K.

    Args:
        relevant_ids: Set of relevant document IDs (ground truth).
        retrieved_ids: Ordered list of retrieved document IDs.
        k: Cutoff rank.

    Returns:
        Recall@K in [0.0, 1.0].
    """
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return len(relevant_ids & top_k) / len(relevant_ids)


def mean_recall_at_k(
    queries: list[dict],
    k: int = 10,
) -> dict[str, float]:
    """Compute mean Recall@K across a set of queries.

    Args:
        queries: List of dicts with 'relevant_ids' and 'retrieved_ids'.
        k: Cutoff rank.

    Returns:
        Dict with 'mean_recall_at_k' and per-query scores.
    """
    scores = [
        recall_at_k(
            set(q["relevant_ids"]),
            q["retrieved_ids"],
            k,
        )
        for q in queries
    ]
    return {
        "mean_recall_at_k": sum(scores) / len(scores) if scores else 0.0,
        "k": k,
        "num_queries": len(queries),
        "per_query": scores,
    }
