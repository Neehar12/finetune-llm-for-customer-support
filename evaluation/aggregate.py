"""Aggregate per-example judge verdicts into summary metrics.

Reads `evaluation_results.jsonl` and writes `aggregate_metrics.json`:
mean of each 1-5 dimension, hallucination rate, and per-category / per-intent
breakdowns for error analysis. Per-example verdicts are always preserved
(in evaluation_results.jsonl) so we can inspect where a model regresses.

Run:
    python evaluation/aggregate.py --model-id qwen3-1.7b-base
"""
import argparse
import json
from collections import defaultdict

import config

SCORE_FIELDS = ("issue_understanding", "correctness", "resolution_quality",
                "support_quality")


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def _mean(xs):
    return round(sum(xs) / len(xs), 3) if xs else None


def summarize(rows):
    out = {f"{field}_mean": _mean([r[field] for r in rows]) for field in SCORE_FIELDS}
    out["hallucination_rate"] = round(
        sum(1 for r in rows if r["hallucination"]) / len(rows), 4
    ) if rows else None
    out["num_evaluated"] = len(rows)
    return out


def run(model_id):
    out_dir = config.EXPERIMENTS_DIR / model_id
    eval_path = out_dir / "evaluation_results.jsonl"
    rows = load_jsonl(eval_path)

    metrics = {"model_id": model_id, "judge_model": config.JUDGE_MODEL}
    metrics.update(summarize(rows))

    by_cat = defaultdict(list)
    by_intent = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
        by_intent[r["intent"]].append(r)

    metrics["per_category"] = {c: summarize(rs) for c, rs in sorted(by_cat.items())}
    metrics["per_intent"] = {i: summarize(rs) for i, rs in sorted(by_intent.items())}

    agg_path = out_dir / "aggregate_metrics.json"
    with open(agg_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n=== {model_id} (n={metrics['num_evaluated']}, judge={config.JUDGE_MODEL}) ===")
    for field in SCORE_FIELDS:
        print(f"  {field:22s} {metrics[field + '_mean']}")
    print(f"  {'hallucination_rate':22s} {metrics['hallucination_rate']}")
    print(f"aggregate -> {agg_path}")
    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", default=config.BASE_MODEL_ID)
    args = ap.parse_args()
    run(args.model_id)


if __name__ == "__main__":
    main()
