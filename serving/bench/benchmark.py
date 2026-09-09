"""Latency / throughput benchmark for the served model (Ollama, Q4_K_M).

Measures the ACTUAL served path (Ollama /api/chat) with the frozen prompt
contract. Uses Ollama's own nanosecond timing fields for well-defined numbers:

  - decode throughput  = eval_count / eval_duration        (tokens/s, generation)
  - prefill throughput = prompt_eval_count / prompt_eval_duration
  - per-request latency = total_duration (excl. one-time model load)
  - system throughput   = total output tokens / wall time, swept over concurrency

    python serving/bench/benchmark.py --model cs-tuned --n 40 --concurrency 1 2 4

Writes bench/results.md and bench/throughput_vs_concurrency.png.
"""
import argparse
import json
import statistics as st
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ollama

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from common.prompting import build_chat_messages, GEN_OPTIONS, THINK  # noqa: E402

HERE = Path(__file__).resolve().parent
BENCH = REPO_ROOT / "evaluation" / "data" / "benchmark" / "test_benchmark.jsonl"


def sample_prompts(n):
    rows = [json.loads(l) for l in open(BENCH)]
    step = max(1, len(rows) // n)
    return [r["instruction"] for r in rows[::step]][:n]


def one_call(client, model, msg):
    r = client.chat(model=model, messages=build_chat_messages(msg),
                    options=GEN_OPTIONS, think=THINK)
    return {
        "total_ms": (r.get("total_duration") or 0) / 1e6,
        "out_tok": r.get("eval_count") or 0,
        "decode_tps": (r["eval_count"] / (r["eval_duration"] / 1e9))
        if r.get("eval_duration") else 0,
        "prefill_tps": (r["prompt_eval_count"] / (r["prompt_eval_duration"] / 1e9))
        if r.get("prompt_eval_duration") else 0,
        "prompt_tok": r.get("prompt_eval_count") or 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="cs-tuned")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--concurrency", type=int, nargs="+", default=[1, 2, 4])
    ap.add_argument("--host", default="http://localhost:11434")
    args = ap.parse_args()
    client = ollama.Client(host=args.host)
    prompts = sample_prompts(args.n)

    print(f"warmup (loads {args.model}) ...")
    client.chat(model=args.model, messages=build_chat_messages("hello"),
                options={**GEN_OPTIONS, "num_predict": 8}, think=THINK)

    # --- single-stream latency + throughput (sequential) --------------------
    print(f"sequential: {len(prompts)} requests ...")
    rows = [one_call(client, args.model, p) for p in prompts]
    lat = sorted(r["total_ms"] for r in rows)
    decode = [r["decode_tps"] for r in rows]
    prefill = [r["prefill_tps"] for r in rows]
    outtok = [r["out_tok"] for r in rows]
    p = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))]
    seq = {
        "n": len(rows),
        "latency_ms_p50": round(st.median(lat), 1),
        "latency_ms_p95": round(p(0.95), 1),
        "latency_ms_mean": round(st.mean(lat), 1),
        "decode_tps_mean": round(st.mean(decode), 1),
        "prefill_tps_mean": round(st.mean(prefill), 1),
        "output_tokens_mean": round(st.mean(outtok), 1),
    }
    print(json.dumps(seq, indent=2))

    # --- throughput vs concurrency ------------------------------------------
    conc_rows = []
    for c in args.concurrency:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=c) as ex:
            res = list(ex.map(lambda pr: one_call(client, args.model, pr), prompts))
        wall = time.perf_counter() - t0
        tot_tok = sum(r["out_tok"] for r in res)
        conc_rows.append({
            "concurrency": c,
            "wall_s": round(wall, 1),
            "req_per_s": round(len(prompts) / wall, 2),
            "system_decode_tps": round(tot_tok / wall, 1),
        })
        print(f"  c={c}: {conc_rows[-1]}")

    # --- write results.md ---------------------------------------------------
    with open(HERE / "results.md", "w") as f:
        f.write(f"# Serving benchmark — `{args.model}` (Q4_K_M, Ollama)\n\n")
        f.write(f"Hardware: local Mac (Apple Metal). n={args.n} prompts sampled across the "
                f"test split. Timings from Ollama's own duration fields.\n\n")
        f.write("## Single-stream latency & throughput\n\n")
        f.write("| metric | value |\n|---|---|\n")
        for k, v in seq.items():
            f.write(f"| {k} | {v} |\n")
        f.write("\n## Throughput vs concurrency\n\n")
        f.write("| concurrency | wall (s) | req/s | system decode tok/s |\n|---|---|---|---|\n")
        for r in conc_rows:
            f.write(f"| {r['concurrency']} | {r['wall_s']} | {r['req_per_s']} | {r['system_decode_tps']} |\n")
        f.write("\n> Concurrency scaling depends on `OLLAMA_NUM_PARALLEL` (default lets Ollama "
                "pick based on memory). Q4_K_M 1.7B is small, so a few parallel slots fit.\n")
    print("wrote", HERE / "results.md")

    # --- plot: throughput vs concurrency ------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        BG, FG = "#1e1e1e", "#e6e6e6"
        plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG,
                             "savefig.facecolor": BG, "text.color": FG, "axes.labelcolor": FG,
                             "xtick.color": FG, "ytick.color": FG, "axes.edgecolor": "#555",
                             "font.family": "monospace"})
        cs = [r["concurrency"] for r in conc_rows]
        fig, ax = plt.subplots(figsize=(6.4, 4.2))
        ax.plot(cs, [r["system_decode_tps"] for r in conc_rows], "-o", color="#59c26b", lw=1.8, ms=9)
        for r in conc_rows:
            ax.annotate(f"{r['system_decode_tps']:.0f}", (r["concurrency"], r["system_decode_tps"]),
                        textcoords="offset points", xytext=(0, 10), ha="center", color=FG)
        ax.set_xticks(cs); ax.set_xlabel("concurrency"); ax.set_ylabel("system decode tok/s")
        ax.set_title(f"Throughput vs concurrency — {args.model} (Q4_K_M)", pad=12)
        ax.grid(color="#333", lw=0.7)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        fig.tight_layout(); fig.savefig(HERE / "throughput_vs_concurrency.png", dpi=150)
        print("wrote", HERE / "throughput_vs_concurrency.png")
    except Exception as e:
        print("plot skipped:", e)


if __name__ == "__main__":
    main()
