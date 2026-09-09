"""Phase 3: establish the base-model benchmark end to end.

Orchestrates: build frozen benchmark (if missing) -> generate base-model
responses -> judge them with Claude Opus 5 -> aggregate metrics. This baseline
is created BEFORE any fine-tuning and is the reference every fine-tuned
checkpoint is compared against.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python evaluation/run_base_benchmark.py
"""
import build_benchmark
import generate
import judge
import aggregate
import config


def main():
    if not config.BENCH_PATH.exists():
        print("[1/4] Building frozen benchmark...")
        build_benchmark.main()
    else:
        print(f"[1/4] Benchmark already frozen at {config.BENCH_PATH} (reusing)")

    out_dir = config.EXPERIMENTS_DIR / config.BASE_MODEL_ID
    print(f"[2/4] Generating base-model responses ({config.BASE_MODEL_TAG})...")
    generate.run(config.BASE_MODEL_TAG, config.BASE_MODEL_ID,
                 config.BENCH_PATH, out_dir)

    print(f"[3/4] Judging with {config.JUDGE_MODEL}...")
    judge.run(config.BASE_MODEL_ID)

    print("[4/4] Aggregating metrics...")
    aggregate.run(config.BASE_MODEL_ID)


if __name__ == "__main__":
    main()
