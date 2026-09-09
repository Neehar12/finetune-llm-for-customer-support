"""Phase 2: build and FREEZE the fixed validation benchmark.

Samples `PER_INTENT` examples from each intent in the validation split
(intent-stratified so all 27 intents are represented), with a fixed seed for
reproducibility. Once frozen, this exact set is used to benchmark the base
model and every fine-tuned checkpoint.

The benchmark is drawn from the VALIDATION split only. The held-out TEST split
is never touched here — it is reserved for the final base-vs-tuned comparison.

Run:
    python evaluation/build_benchmark.py
"""
import json
import random
from collections import defaultdict

import config


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def main():
    rows = load_jsonl(config.VAL_PATH)

    by_intent = defaultdict(list)
    for r in rows:
        by_intent[r["intent"]].append(r)

    rng = random.Random(config.SEED)
    benchmark = []
    for intent in sorted(by_intent):
        pool = sorted(by_intent[intent], key=lambda r: r["instruction"])
        rng.shuffle(pool)
        chosen = pool[: config.PER_INTENT]
        for r in chosen:
            benchmark.append(r)

    # Stable ids and a trimmed record shape.
    benchmark.sort(key=lambda r: (r["intent"], r["instruction"]))
    items = []
    for i, r in enumerate(benchmark):
        items.append({
            "id": f"val_{i:04d}",
            "intent": r["intent"],
            "category": r["category"],
            "flags": r.get("flags", ""),
            "group": r.get("group"),
            "instruction": r["instruction"],
            "reference_response": r["response"],
        })

    config.BENCH_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.BENCH_PATH, "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    per_intent = defaultdict(int)
    per_category = defaultdict(int)
    for it in items:
        per_intent[it["intent"]] += 1
        per_category[it["category"]] += 1

    meta = {
        "source_split": str(config.VAL_PATH.relative_to(config.REPO_ROOT)),
        "seed": config.SEED,
        "per_intent_target": config.PER_INTENT,
        "num_items": len(items),
        "num_intents": len(per_intent),
        "num_categories": len(per_category),
        "per_intent_counts": dict(sorted(per_intent.items())),
        "per_category_counts": dict(sorted(per_category.items())),
    }
    with open(config.BENCH_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Froze {len(items)} benchmark items -> {config.BENCH_PATH}")
    print(f"  {meta['num_intents']} intents, {meta['num_categories']} categories")
    print(f"  meta -> {config.BENCH_META_PATH}")


if __name__ == "__main__":
    main()
