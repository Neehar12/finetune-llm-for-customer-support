"""Generate model responses for the frozen benchmark.

Runs any Ollama-served model over the benchmark using the frozen prompt
contract (`common.prompting`) and fixed generation settings. Writes one
`generations.jsonl` record per benchmark item.

Used for the base model now, and for the fine-tuned model later (same code,
different Ollama tag) so the comparison stays apples-to-apples.

Run (base model):
    python evaluation/generate.py
"""
import argparse
import json
import re

import ollama

import config

_THINK_RE = re.compile(r"^\s*<think>.*?</think>\s*", re.DOTALL)


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def strip_think(text: str) -> str:
    """Remove a leading <think>...</think> block if the model emits one anyway."""
    return _THINK_RE.sub("", text).strip()


def generate_one(client, model_tag, instruction):
    messages = config.build_chat_messages(instruction)
    kwargs = dict(model=model_tag, messages=messages, options=config.GEN_OPTIONS)
    try:
        resp = client.chat(think=config.THINK, **kwargs)
    except TypeError:
        # Older ollama-python without the `think` kwarg: fall back and strip tags.
        resp = client.chat(**kwargs)
    content = resp["message"]["content"]
    return strip_think(content)


def run(model_tag, model_id, benchmark_path, out_dir):
    items = load_jsonl(benchmark_path)
    client = ollama.Client(host=config.OLLAMA_HOST)

    out_dir.mkdir(parents=True, exist_ok=True)
    gen_path = out_dir / "generations.jsonl"

    with open(gen_path, "w") as f:
        for i, it in enumerate(items, 1):
            text = generate_one(client, model_tag, it["instruction"])
            rec = {
                "id": it["id"],
                "intent": it["intent"],
                "category": it["category"],
                "instruction": it["instruction"],
                "reference_response": it["reference_response"],
                "generated_response": text,
                "model_id": model_id,
                "model_tag": model_tag,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if i % 10 == 0 or i == len(items):
                print(f"  generated {i}/{len(items)}")

    # Record exactly how these were generated (experiment metadata).
    meta = {
        "model_id": model_id,
        "model_tag": model_tag,
        "num_items": len(items),
        "benchmark": str(benchmark_path.relative_to(config.REPO_ROOT)),
        "system_prompt": config.SYSTEM_PROMPT,
        "think": config.THINK,
        "gen_options": config.GEN_OPTIONS,
    }
    with open(out_dir / "generation_config.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {len(items)} generations -> {gen_path}")
    return gen_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-tag", default=config.BASE_MODEL_TAG)
    ap.add_argument("--model-id", default=config.BASE_MODEL_ID)
    ap.add_argument("--benchmark", default=str(config.BENCH_PATH))
    args = ap.parse_args()

    from pathlib import Path
    out_dir = config.EXPERIMENTS_DIR / args.model_id
    run(args.model_tag, args.model_id, Path(args.benchmark), out_dir)


if __name__ == "__main__":
    main()
