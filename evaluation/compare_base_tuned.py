"""Final base-vs-tuned comparison on the untouched 1,100-item test split.

Both models were served at identical Q4_K_M/Ollama fidelity and judged by Opus 5
(v2 rubric). This script turns the two judged experiments into the graded
deliverable: delta tables (overall / per-category), base-vs-tuned plots, and
extracted failure + win cases (side-by-side).

    /usr/local/bin/python3 evaluation/compare_base_tuned.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config

EXP = config.EXPERIMENTS_DIR
BASE_ID, TUNED_ID = "qwen3-1.7b-base-test", "qwen3-1.7b-tuned-test"
OUT = config.REPO_ROOT / "evaluation" / "results"
(OUT / "plots").mkdir(parents=True, exist_ok=True)
(OUT / "data").mkdir(parents=True, exist_ok=True)

METRICS = [("resolution_quality", "resolution", True),
           ("correctness", "correctness", True),
           ("issue_understanding", "understanding", True),
           ("support_quality", "support", True),
           ("hallucination_rate", "hallucination", False)]


def load(mid):
    agg = json.load(open(EXP / f"{mid}-judge-v2" / "aggregate_metrics.json"))
    res = [json.loads(l) for l in open(EXP / f"{mid}-judge-v2" / "evaluation_results.jsonl")]
    gen = {g["id"]: g for g in (json.loads(l) for l in open(EXP / mid / "generations.jsonl"))}
    return agg, {r["id"]: r for r in res}, gen


base_agg, base_res, base_gen = load(BASE_ID)
tuned_agg, tuned_res, tuned_gen = load(TUNED_ID)

# ---- overall + per-category delta tables -----------------------------------
def row(a):
    return {m: a[f"{m}_mean"] if m != "hallucination_rate" else a[m]
            for m, _, _ in METRICS}

comparison = {"overall": {"base": row(base_agg), "tuned": row(tuned_agg)}, "per_category": {}}
for cat in base_agg["per_category"]:
    comparison["per_category"][cat] = {
        "base": row(base_agg["per_category"][cat]),
        "tuned": row(tuned_agg["per_category"][cat]),
        "n": tuned_agg["per_category"][cat]["num_evaluated"],
    }
json.dump(comparison, open(OUT / "data" / "comparison.json", "w"), indent=2)

# ---- plots (dark theme, base vs tuned) -------------------------------------
BG, FG = "#1e1e1e", "#e6e6e6"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                     "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG,
                     "ytick.color": FG, "axes.edgecolor": "#555", "font.family": "monospace"})
BASE_C, TUNED_C = "#8a8a8a", "#59c26b"


def grouped_bar(fname, labels, base_vals, tuned_vals, ylabel, title, ylim, pct=False):
    import numpy as np
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 1.1), 4.6))
    b1 = ax.bar(x - w / 2, base_vals, w, label="base", color=BASE_C)
    b2 = ax.bar(x + w / 2, tuned_vals, w, label="tuned", color=TUNED_C)
    for bars in (b1, b2):
        for r in bars:
            h = r.get_height()
            ax.annotate(f"{h:.0%}" if pct else f"{h:.2f}", (r.get_x() + r.get_width() / 2, h),
                        textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8, color=FG)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=0 if len(labels) <= 6 else 45, ha="center" if len(labels) <= 6 else "right", fontsize=9)
    ax.set_ylim(*ylim); ax.set_ylabel(ylabel); ax.set_title(title, pad=12)
    ax.grid(axis="y", color="#333", lw=0.7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(facecolor=BG, edgecolor="#555", labelcolor=FG)
    fig.tight_layout(); fig.savefig(OUT / "plots" / fname, dpi=150); plt.close(fig)
    print("wrote", OUT / "plots" / fname)


# overall metrics (1-5) + hallucination separately
q = [(m, sh) for m, sh, hi in METRICS if hi]
grouped_bar("overall_quality.png", [sh for _, sh in q],
            [row(base_agg)[m] for m, _ in q], [row(tuned_agg)[m] for m, _ in q],
            "score (1-5)", "Overall quality — base vs tuned (test, n=1100)", (0, 5))
grouped_bar("overall_hallucination.png", ["hallucination rate"],
            [base_agg["hallucination_rate"]], [tuned_agg["hallucination_rate"]],
            "rate", "Hallucination rate — base vs tuned (lower is better)", (0, 0.5), pct=True)

cats = list(comparison["per_category"].keys())
grouped_bar("resolution_by_category.png", cats,
            [comparison["per_category"][c]["base"]["resolution_quality"] for c in cats],
            [comparison["per_category"][c]["tuned"]["resolution_quality"] for c in cats],
            "resolution (1-5)", "Resolution quality by category", (0, 5))
grouped_bar("hallucination_by_category.png", cats,
            [comparison["per_category"][c]["base"]["hallucination_rate"] for c in cats],
            [comparison["per_category"][c]["tuned"]["hallucination_rate"] for c in cats],
            "hallucination rate", "Hallucination rate by category (lower is better)", (0, 1.0), pct=True)

# ---- failure cases (tuned) + win cases (tuned fixes base) -------------------
def item(mid_res, mid_gen, _id):
    r, g = mid_res[_id], mid_gen[_id]
    return {"scores": {k: r[k] for k in ("issue_understanding", "correctness",
            "resolution_quality", "support_quality", "hallucination")},
            "reason": r["reason"], "response": g["generated_response"],
            "instruction": g["instruction"], "reference": g["reference_response"],
            "intent": g["intent"], "category": g["category"]}

# tuned still-fails: hallucination or resolution <= 2
tuned_fail_ids = [i for i, r in tuned_res.items()
                  if r["hallucination"] or r["resolution_quality"] <= 2]
# tuned fixes base: base hallucinated -> tuned did not, or resolution jump >= 2
win_ids = sorted(i for i in tuned_res
                 if (base_res[i]["hallucination"] and not tuned_res[i]["hallucination"])
                 or (tuned_res[i]["resolution_quality"] - base_res[i]["resolution_quality"] >= 2))

# CANCEL (check_cancellation_fee) is the ONLY category where hallucination did NOT
# improve (33% -> 33%); surface it explicitly, preferring cases where BASE also
# hallucinated (clearest "no improvement") over ones tuning newly broke.
cancel_fail = sorted((i for i in tuned_fail_ids if tuned_res[i]["category"] == "CANCEL"),
                     key=lambda i: (not base_res[i]["hallucination"], i))
other_fail = sorted(i for i in tuned_fail_ids if tuned_res[i]["category"] != "CANCEL")


def _case_block(f, _id):
    b, t = item(base_res, base_gen, _id), item(tuned_res, tuned_gen, _id)
    f.write(f"### `{_id}` — {t['intent']} ({t['category']})\n\n")
    f.write(f"**Customer:** {t['instruction']}\n\n")
    f.write(f"**BASE** {b['scores']}\n\n> {b['response'][:600]}\n\n")
    f.write(f"**TUNED** {t['scores']}\n\n> {t['response'][:600]}\n\n")
    f.write(f"**Judge (tuned):** {t['reason'][:400]}\n\n")
    f.write(f"**Reference:** {t['reference'][:400]}\n\n---\n\n")


def dump_sections(fname, title, sections):
    with open(OUT / fname, "w") as f:
        f.write(f"# {title}\n\n(test split, Q4_K_M/Ollama, Opus-5 v2 judge)\n\n")
        for header, ids in sections:
            if not ids:
                continue
            f.write(f"## {header}\n\n")
            for _id in ids:
                _case_block(f, _id)
    print("wrote", OUT / fname)


dump_sections("failure_cases.md", "Failure cases — where the tuned model still struggles", [
    ("CANCEL — the one category where hallucination did NOT improve (33% -> 33%)", cancel_fail[:4]),
    ("Other residual failures", other_fail[:6]),
])
dump_sections("win_cases.md", "Win cases — where fine-tuning fixed the base model",
              [("Base hallucinated / low-resolution -> tuned fixed it", win_ids[:10])])
print(f"\npools: tuned_failures={len(tuned_fail_ids)} (CANCEL={len(cancel_fail)}), "
      f"wins={len(win_ids)}  (of 1100)")
