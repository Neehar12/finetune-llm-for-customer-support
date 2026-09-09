"""Generate the checkpoint-selection plots (Task 2/3).

Reads the judged selection metrics + training curves and renders one dot-plot
per metric across Base -> E1 -> E2 -> E3, plus a combined quality panel and the
train/val-loss curve. Pure-stdlib inputs, matplotlib output. Reproducible:

    /usr/local/bin/python3 finetuning/results/plot_metrics.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
PLOTS = HERE / "plots"
PLOTS.mkdir(exist_ok=True)

sel = json.load(open(DATA / "checkpoint_selection.json"))
train = json.load(open(DATA / "training_metrics.json"))

# ---- assemble series in Base, E1, E2, E3 order -----------------------------
base = sel["base_fp16"]
rows = sorted(sel["rows"], key=lambda r: r["epoch"])
X = ["Base", "E1", "E2", "E3"]


def series(key):
    return [base[key]] + [r[key] for r in rows]


# ---- screenshot-style theme ------------------------------------------------
BG = "#1e1e1e"
FG = "#e6e6e6"
DOT = "#ffffff"
ACCENT = "#4ea1ff"
GOOD = "#59c26b"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
    "axes.edgecolor": "#555555", "font.family": "monospace", "font.size": 12,
})


def dot_plot(fname, y, ylabel, title, ylim, higher_better=True,
             highlight_last=True, fmt="{:.2f}", value_labels=True, xlabels=X):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    xs = list(range(len(xlabels)))
    ax.plot(xs, y, color="#555555", lw=1.2, zorder=1)          # faint trend line
    colors = [DOT] * len(y)
    if highlight_last:
        colors[-1] = GOOD if higher_better else GOOD
    ax.scatter(xs, y, s=170, color=colors, edgecolors="none", zorder=3)
    if value_labels:
        for xi, yi in zip(xs, y):
            ax.annotate(fmt.format(yi), (xi, yi), textcoords="offset points",
                        xytext=(0, 12), ha="center", fontsize=11, color=FG)
    ax.set_xticks(xs); ax.set_xticklabels(xlabels)
    ax.set_xlim(-0.5, len(xlabels) - 0.5)
    ax.set_ylim(*ylim)
    ax.set_ylabel(ylabel)
    dirn = "higher is better" if higher_better else "lower is better"
    ax.set_title(f"{title}   ({dirn})", fontsize=12, pad=12)
    ax.grid(axis="y", color="#333333", lw=0.7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(PLOTS / fname, dpi=150)
    plt.close(fig)
    print("wrote", PLOTS / fname)


# ---- per-metric plots (1-5 quality metrics) --------------------------------
dot_plot("resolution_quality.png", series("resolution"), "resolution (1-5)",
         "Resolution quality", (1, 5))
dot_plot("correctness.png", series("correctness"), "correctness (1-5)",
         "Correctness", (1, 5))
dot_plot("issue_understanding.png", series("understanding"), "understanding (1-5)",
         "Issue understanding", (1, 5))
dot_plot("support_quality.png", series("support"), "support tone (1-5)",
         "Support quality", (1, 5))

# ---- hallucination (rate, lower better) ------------------------------------
dot_plot("hallucination_rate.png", series("hallucination"), "hallucination rate",
         "Hallucination rate", (0, 0.45), higher_better=False, fmt="{:.1%}")

# ---- eval loss (epochs only, lower better) ---------------------------------
evl = train["eval_loss_by_epoch"]
dot_plot("eval_loss.png", [evl["1"], evl["2"], evl["3"]], "eval loss",
         "Validation loss", (0.55, 0.61), higher_better=False,
         fmt="{:.4f}", xlabels=["E1", "E2", "E3"])

# ---- combined quality panel (all four 1-5 metrics) -------------------------
fig, ax = plt.subplots(figsize=(7.6, 4.6))
xs = list(range(4))
metrics = [("resolution", ACCENT), ("correctness", GOOD),
           ("understanding", "#e0b34e"), ("support", "#c77dff")]
for key, col in metrics:
    ax.plot(xs, series(key), "-o", color=col, lw=1.6, ms=8, label=key)
ax.set_xticks(xs); ax.set_xticklabels(X)
ax.set_ylim(1, 5); ax.set_ylabel("score (1-5)")
ax.set_title("All quality metrics (higher is better)", fontsize=12, pad=12)
ax.grid(axis="y", color="#333333", lw=0.7)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(facecolor=BG, edgecolor="#555555", labelcolor=FG, fontsize=10, loc="lower right")
fig.tight_layout(); fig.savefig(PLOTS / "quality_combined.png", dpi=150)
plt.close(fig); print("wrote", PLOTS / "quality_combined.png")

# ---- train vs val loss by epoch --------------------------------------------
tr = train["train_loss_by_epoch"]
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ep = [1, 2, 3]
ax.plot(ep, [tr["1"], tr["2"], tr["3"]], "-o", color=ACCENT, lw=1.6, ms=8, label="train loss")
ax.plot(ep, [evl["1"], evl["2"], evl["3"]], "-o", color=GOOD, lw=1.6, ms=8, label="val loss")
ax.set_xticks(ep); ax.set_xticklabels(["E1", "E2", "E3"])
ax.set_ylabel("loss"); ax.set_title("Train vs validation loss (lower is better)", fontsize=12, pad=12)
ax.grid(axis="y", color="#333333", lw=0.7)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(facecolor=BG, edgecolor="#555555", labelcolor=FG, fontsize=10)
fig.tight_layout(); fig.savefig(PLOTS / "train_val_loss.png", dpi=150)
plt.close(fig); print("wrote", PLOTS / "train_val_loss.png")
