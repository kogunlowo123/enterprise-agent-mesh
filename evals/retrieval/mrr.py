"""Mean Reciprocal Rank (MRR) evaluation metric."""

from __future__ import annotations


def reciprocal_rank(relevant_ids: set[str], retrieved_ids: list[str]) -> float:
    """Compute Reciprocal Rank for a single query."""
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(queries: list[dict]) -> dict[str, float]:
    """Compute MRR across a set of queries."""
    scores = [
        reciprocal_rank(set(q["relevant_ids"]), q["retrieved_ids"])
        for q in queries
    ]
    return {
        "mrr": sum(scores) / len(scores) if scores else 0.0,
        "num_queries": len(queries),
        "per_query": scores,
    }
