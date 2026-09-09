"""Render a human-readable RESULTS.md for a benchmarked model.

Reads an experiment directory (generations + verdicts + aggregate + config)
and writes a self-contained Markdown report: overall metrics, per-category and
per-intent breakdowns, generation/judge config, and a few qualitative examples
(best and worst by total score). Reusable for the base model and every
fine-tuned checkpoint.

Run:
    python report.py --model-id qwen3-1.7b-base
"""
import argparse
import json

import config

SCORE_FIELDS = ("issue_understanding", "correctness", "resolution_quality",
                "support_quality")


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def _row(name, s):
    return (f"| {name} | {s['num_evaluated']} | {s['issue_understanding_mean']} | "
            f"{s['correctness_mean']} | {s['resolution_quality_mean']} | "
            f"{s['support_quality_mean']} | {s['hallucination_rate']} |")


def _example_block(g, e):
    scores = " · ".join(f"{k.split('_')[0]}={e[k]}" for k in SCORE_FIELDS)
    return (
        f"**intent:** `{g['intent']}`  ·  **category:** `{g['category']}`\n\n"
        f"- **Customer:** {g['instruction']}\n"
        f"- **Reference:** {g['reference_response']}\n"
        f"- **Base output:** {g['generated_response']}\n"
        f"- **Judge:** {scores} · hallucination=**{e['hallucination']}**\n"
        f"- **Reason:** {e['reason']}\n"
    )


def run(model_id):
    d = config.EXPERIMENTS_DIR / model_id
    agg = json.load(open(d / "aggregate_metrics.json"))
    gcfg = json.load(open(d / "generation_config.json"))
    gens = {r["id"]: r for r in load_jsonl(d / "generations.jsonl")}
    evs = {r["id"]: r for r in load_jsonl(d / "evaluation_results.jsonl")}

    def total(e):
        return sum(e[k] for k in SCORE_FIELDS)

    order = sorted(evs, key=lambda i: total(evs[i]))
    weak = order[:2]
    strong = [i for i in reversed(order) if not evs[i]["hallucination"]][:2]

    lines = []
    lines.append(f"# Benchmark report — `{model_id}`\n")
    lines.append(f"- **Model:** `{gcfg['model_tag']}` (served via Ollama)")
    lines.append(f"- **Judge:** `{agg['judge_model']}`")
    lines.append(f"- **Benchmark:** {gcfg['benchmark']} "
                 f"({agg['num_evaluated']} items, validation split, frozen)")
    lines.append(f"- **Thinking:** {gcfg['think']}  ·  **Generation:** "
                 f"`{json.dumps(gcfg['gen_options'])}`")
    lines.append(f"- **System prompt:** {gcfg['system_prompt']}\n")

    lines.append("## Overall\n")
    lines.append("| metric | n | understanding | correctness | resolution | support | halluc. rate |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append(_row("**overall**", agg))
    lines.append("")

    lines.append("## By category (sorted by resolution quality)\n")
    lines.append("| category | n | understanding | correctness | resolution | support | halluc. rate |")
    lines.append("|---|---|---|---|---|---|---|")
    for cat, s in sorted(agg["per_category"].items(),
                         key=lambda kv: kv[1]["resolution_quality_mean"]):
        lines.append(_row(cat, s))
    lines.append("")

    lines.append("## By intent (sorted by resolution quality)\n")
    lines.append("| intent | n | understanding | correctness | resolution | support | halluc. rate |")
    lines.append("|---|---|---|---|---|---|---|")
    for it, s in sorted(agg["per_intent"].items(),
                        key=lambda kv: kv[1]["resolution_quality_mean"]):
        lines.append(_row(it, s))
    lines.append("")

    lines.append("## Example cases\n")
    lines.append("### Strongest\n")
    for i in strong:
        lines.append(_example_block(gens[i], evs[i]))
    lines.append("### Weakest\n")
    for i in weak:
        lines.append(_example_block(gens[i], evs[i]))

    lines.append("\n---\n_Raw artifacts in this folder: `generations.jsonl`, "
                 "`evaluation_results.jsonl` (per-example scores + reasons), "
                 "`aggregate_metrics.json`, `generation_config.json`._\n")

    out = d / "RESULTS.md"
    out.write_text("\n".join(lines))
    print(f"Wrote report -> {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", default=config.BASE_MODEL_ID)
    args = ap.parse_args()
    run(args.model_id)


if __name__ == "__main__":
    main()
