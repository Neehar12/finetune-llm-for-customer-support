"""Tier-2 checkpoint selection (run locally, after downloading Kaggle outputs).

For each epoch's frozen-benchmark generations, run the Opus-5 v2 judge + aggregate
(via the evaluation harness, in a subprocess so its own `config` resolves), then
rank epochs by the guide's priority:

    resolution_quality -> correctness -> (low) hallucination -> (low) val loss

Prereqs:
    export ANTHROPIC_API_KEY=...  ANTHROPIC_WORKSPACE_ID=...
    # `outputs/` = the folder downloaded from Kaggle (epoch_*/generations.jsonl,
    #  run_manifest.json)

    python finetuning/select_checkpoint.py --outputs finetuning/outputs
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import config  # finetuning config (REPO_ROOT, MODEL_ID)

EVAL_DIR = config.REPO_ROOT / "evaluation"
EXPERIMENTS_DIR = EVAL_DIR / "experiments"


def _run(cmd):
    print("  $", " ".join(cmd))
    subprocess.run(cmd, cwd=str(EVAL_DIR), check=True)


def judge_and_aggregate(gen_src, exp_id, prompt_version):
    """Copy generations into an experiment dir, run the v2 judge + aggregate,
    and return the aggregate metrics dict."""
    exp_dir = EXPERIMENTS_DIR / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gen_src, exp_dir / "generations.jsonl")
    _run([sys.executable, "judge.py", "--model-id", exp_id,
          "--prompt-version", prompt_version])
    judged_id = f"{exp_id}-judge-{prompt_version}"
    _run([sys.executable, "aggregate.py", "--model-id", judged_id])
    agg = json.load(open(EXPERIMENTS_DIR / judged_id / "aggregate_metrics.json"))
    return {
        "resolution": agg["resolution_quality_mean"],
        "correctness": agg["correctness_mean"],
        "understanding": agg["issue_understanding_mean"],
        "support": agg["support_quality_mean"],
        "hallucination": agg["hallucination_rate"],
        "experiment": judged_id,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs", default=str(config.OUTPUT_DIR),
                    help="Downloaded Kaggle outputs dir")
    ap.add_argument("--model-id", default=config.MODEL_ID)
    ap.add_argument("--prompt-version", default="v2")
    args = ap.parse_args()

    outputs = Path(args.outputs)
    manifest = json.load(open(outputs / "run_manifest.json"))
    loss_by_epoch = {e["epoch"]: e.get("eval_loss") for e in manifest["epochs"]}

    # fp16 base reference (no adapter) — matched to the epoch generation path.
    base = None
    base_src = outputs / "base_fp16" / "generations.jsonl"
    if base_src.exists():
        print("\n=== base (fp16, no adapter) ===")
        base = judge_and_aggregate(base_src, f"{args.model_id}-base-fp16", args.prompt_version)
        base["epoch"] = "base"
        base["eval_loss"] = None

    rows = []
    for e in manifest["epochs"]:
        k = e["epoch"]
        gen_src = outputs / f"epoch_{k}" / "generations.jsonl"
        if not gen_src.exists():
            print(f"epoch {k}: no generations, skipping")
            continue
        print(f"\n=== epoch {k} (eval_loss={loss_by_epoch.get(k)}) ===")
        r = judge_and_aggregate(gen_src, f"{args.model_id}-epoch{k}", args.prompt_version)
        r["epoch"] = k
        r["eval_loss"] = loss_by_epoch.get(k)
        rows.append(r)

    # Rank: resolution desc, correctness desc, hallucination asc, val loss asc.
    ranked = sorted(rows, key=lambda r: (
        -r["resolution"], -r["correctness"], r["hallucination"],
        r["eval_loss"] if r["eval_loss"] is not None else 1e9,
    ))

    def fmt(r, dref=None):
        def d(k):
            return "" if dref is None else f" ({r[k]-dref[k]:+.2f})"
        return (f"{str(r['epoch']):>5} {r['resolution']:>6.3f}{d('resolution'):>8} "
                f"{r['correctness']:>6.3f}{d('correctness'):>8} "
                f"{r['understanding']:>6.3f} {r['support']:>6.3f} "
                f"{r['hallucination']:>7.3f}{d('hallucination'):>8} "
                f"{(r['eval_loss'] or 0):>8.4f}")

    print("\n================ CHECKPOINT SELECTION (Δ vs fp16 base) ================")
    print(f"{'epoch':>5} {'reso':>6} {'Δreso':>8} {'corr':>6} {'Δcorr':>8} "
          f"{'under':>6} {'supp':>6} {'halluc':>7} {'Δhal':>8} {'valloss':>8}")
    if base:
        print(fmt(base))
    for r in rows:
        print(fmt(r, base))

    best = ranked[0]
    adapter = [e["checkpoint_dir"] for e in manifest["epochs"] if e["epoch"] == best["epoch"]][0]
    print(f"\nSelected epoch {best['epoch']}  (adapter: {adapter})")
    print("Merge THIS adapter into the fp16 base, convert to GGUF, quantize Q4_K_M, "
          "load into Ollama, then run the final base-vs-tuned TEST comparison.")

    with open(EXPERIMENTS_DIR / f"{args.model_id}_checkpoint_selection.json", "w") as f:
        json.dump({"base_fp16": base, "rows": rows, "selected_epoch": best["epoch"]}, f, indent=2)


if __name__ == "__main__":
    main()
