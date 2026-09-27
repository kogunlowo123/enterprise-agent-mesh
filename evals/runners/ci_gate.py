"""CI evaluation gate - fails CI if evals fall below thresholds."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from evals.retrieval.mrr import mean_reciprocal_rank
from evals.retrieval.recall_at_k import mean_recall_at_k


THRESHOLDS = {
    "recall_at_10": 0.80,
    "mrr": 0.70,
}


def run_ci_gate(dataset_path: Path) -> int:
    """Run eval gate against dataset. Returns exit code (0=pass, 1=fail)."""
    with dataset_path.open() as f:
        queries = [json.loads(line) for line in f if line.strip()]

    recall_result = mean_recall_at_k(queries, k=10)
    mrr_result = mean_reciprocal_rank(queries)

    results = {
        "recall_at_10": recall_result["mean_recall_at_k"],
        "mrr": mrr_result["mrr"],
    }

    failed = False
    for metric, threshold in THRESHOLDS.items():
        value = results[metric]
        status = "PASS" if value >= threshold else "FAIL"
        print(f"{status}: {metric} = {value:.3f} (threshold: {threshold})")
        if value < threshold:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    dataset = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "evals/datasets/golden/mesh-routing-qa-pairs.jsonl"
    )
    sys.exit(run_ci_gate(dataset))
