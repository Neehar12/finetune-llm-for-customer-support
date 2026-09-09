"""Build the FINAL test benchmark (all 1,100 held-out test rows).

Unlike val_benchmark (5 per intent, for cheap iteration/selection), the final
base-vs-tuned claim runs on the ENTIRE untouched test split. This just reshapes
data_cleaning/.../test.jsonl into the record format generate.py/judge.py expect.

    python evaluation/build_test_benchmark.py
"""
import json
from pathlib import Path

import config  # evaluation config (REPO_ROOT, BENCH_DIR)

TEST_SRC = config.REPO_ROOT / "data_cleaning" / "data" / "splits" / "test.jsonl"
OUT = config.BENCH_DIR / "test_benchmark.jsonl"


def main():
    rows = [json.loads(l) for l in open(TEST_SRC)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for i, r in enumerate(rows):
            rec = {
                "id": f"test-{i:04d}",
                "intent": r["intent"],
                "category": r["category"],
                "instruction": r["instruction"],
                "reference_response": r["response"],
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} items -> {OUT.relative_to(config.REPO_ROOT)}")


if __name__ == "__main__":
    main()
