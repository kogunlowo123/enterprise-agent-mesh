"""Citation accuracy evaluation."""

from __future__ import annotations

import re


def extract_citations(text: str) -> list[str]:
    """Extract citation references like [1], [Doc-1], etc."""
    return re.findall(r"\[([^\]]+)\]", text)


def citation_accuracy(
    answer: str,
    valid_citation_ids: set[str],
) -> float:
    """Fraction of citations in answer that are valid."""
    citations = extract_citations(answer)
    if not citations:
        return 1.0  # No citations = no invalid citations

    valid = sum(1 for c in citations if c in valid_citation_ids)
    return valid / len(citations)


def batch_citation_accuracy(
    answers: list[str],
    valid_ids_per_query: list[set[str]],
) -> dict[str, float]:
    """Compute mean citation accuracy for a batch."""
    scores = [
        citation_accuracy(a, v)
        for a, v in zip(answers, valid_ids_per_query)
    ]
    return {
        "mean_citation_accuracy": sum(scores) / len(scores) if scores else 0.0,
        "num_answers": len(answers),
    }
