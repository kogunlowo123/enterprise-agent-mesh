"""Faithfulness evaluation - checks if answer is grounded in context."""

from __future__ import annotations


def faithfulness_score(answer: str, context_chunks: list[str]) -> float:
    """Estimate faithfulness of answer relative to context chunks.

    A simple token-overlap heuristic. Production systems should use
    an LLM judge for more accurate evaluation.
    """
    if not answer or not context_chunks:
        return 0.0

    answer_tokens = set(answer.lower().split())
    context_tokens = set(" ".join(context_chunks).lower().split())

    if not answer_tokens:
        return 0.0

    overlap = answer_tokens & context_tokens
    return len(overlap) / len(answer_tokens)


def batch_faithfulness(
    answers: list[str],
    contexts: list[list[str]],
) -> dict[str, float]:
    """Compute mean faithfulness for a batch of answers."""
    if len(answers) != len(contexts):
        raise ValueError("answers and contexts must have same length")

    scores = [faithfulness_score(a, c) for a, c in zip(answers, contexts)]
    return {
        "mean_faithfulness": sum(scores) / len(scores) if scores else 0.0,
        "num_answers": len(answers),
        "per_answer": scores,
    }
