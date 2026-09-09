"""LLM-as-a-judge: score generations with Claude Opus 5.

Reads a `generations.jsonl`, scores each candidate answer against the frozen
rubric (`prompts.py`) using structured JSON output, and writes
`evaluation_results.jsonl` (one verdict per item). Judge calls run in parallel.

Requires ANTHROPIC_API_KEY in the environment:
    export ANTHROPIC_API_KEY=sk-ant-...
    python evaluation/judge.py --model-id qwen3-1.7b-base
"""
import argparse
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

import config
import prompts
import prompts_v2

# Selectable judge-prompt versions. v1 = original; v2 = explicit dimension
# boundaries. Same schema/scales, so runs are directly comparable.
PROMPTS = {
    "v1": (prompts.JUDGE_SYSTEM, prompts.build_judge_user_message),
    "v2": (prompts_v2.JUDGE_SYSTEM, prompts_v2.build_judge_user_message),
}

# JSON schema for the structured verdict. 1-5 scores as enums (numeric range
# constraints aren't supported by structured outputs, enums are).
VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "issue_understanding": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "correctness": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "resolution_quality": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "hallucination": {"type": "boolean"},
        "support_quality": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "reason": {"type": "string"},
    },
    "required": [
        "issue_understanding", "correctness", "resolution_quality",
        "hallucination", "support_quality", "reason",
    ],
    "additionalProperties": False,
}

_SCORE_FIELDS = ("issue_understanding", "correctness", "resolution_quality",
                 "support_quality")


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def _make_client():
    """Anthropic client. Org-scoped keys need a workspace id header; supply it
    via ANTHROPIC_WORKSPACE_ID (workspace-scoped keys don't need it)."""
    ws = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    headers = {"anthropic-workspace-id": ws} if ws else {}
    return anthropic.Anthropic(default_headers=headers)


def judge_one(client, rec, judge_system, build_fn):
    user_msg = build_fn(
        rec["instruction"], rec["reference_response"], rec["generated_response"],
    )
    resp = client.messages.create(
        model=config.JUDGE_MODEL,
        max_tokens=config.JUDGE_MAX_TOKENS,
        system=judge_system,
        messages=[{"role": "user", "content": user_msg}],
        output_config={
            "format": {"type": "json_schema", "schema": VERDICT_SCHEMA},
            "effort": config.JUDGE_EFFORT,
        },
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"judge refused on {rec['id']}: {resp.stop_details}")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError(f"judge hit max_tokens on {rec['id']} (raise JUDGE_MAX_TOKENS)")

    text = next(b.text for b in resp.content if b.type == "text")
    verdict = json.loads(text)

    out = {
        "id": rec["id"],
        "intent": rec["intent"],
        "category": rec["category"],
    }
    out.update({k: verdict[k] for k in VERDICT_SCHEMA["properties"]})
    return out


def run(model_id, prompt_version="v1"):
    if prompt_version not in PROMPTS:
        sys.exit(f"Unknown prompt version {prompt_version!r}; choose from {list(PROMPTS)}")
    judge_system, build_fn = PROMPTS[prompt_version]

    gen_dir = config.EXPERIMENTS_DIR / model_id
    gen_path = gen_dir / "generations.jsonl"
    if not gen_path.exists():
        sys.exit(f"No generations at {gen_path} — run generate.py first.")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Run:\n  export ANTHROPIC_API_KEY=sk-ant-...")

    # v1 writes in place (backward compatible). Any other version gets its own
    # self-contained experiment dir so v1 results are never overwritten; we copy
    # the (identical) generations across so downstream tools work unchanged.
    if prompt_version == "v1":
        out_dir = gen_dir
    else:
        out_dir = config.EXPERIMENTS_DIR / f"{model_id}-judge-{prompt_version}"
        out_dir.mkdir(parents=True, exist_ok=True)
        for fn in ("generations.jsonl", "generation_config.json"):
            if (gen_dir / fn).exists():
                shutil.copy2(gen_dir / fn, out_dir / fn)

    records = load_jsonl(gen_path)
    client = _make_client()  # SDK default retries handle transient errors

    results = {}
    errors = {}
    with ThreadPoolExecutor(max_workers=config.JUDGE_WORKERS) as ex:
        futures = {ex.submit(judge_one, client, r, judge_system, build_fn): r["id"]
                   for r in records}
        done = 0
        for fut in as_completed(futures):
            rid = futures[fut]
            try:
                res = fut.result()
                results[res["id"]] = res
            except Exception as e:  # noqa: BLE001 — record and continue
                errors[rid] = str(e)
            done += 1
            if done % 10 == 0 or done == len(records):
                print(f"  judged {done}/{len(records)}")

    # Preserve input order.
    ordered = [results[r["id"]] for r in records if r["id"] in results]
    eval_path = out_dir / "evaluation_results.jsonl"
    with open(eval_path, "w") as f:
        for r in ordered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if errors:
        with open(out_dir / "judge_errors.json", "w") as f:
            json.dump(errors, f, indent=2)
        print(f"WARNING: {len(errors)} judge calls failed (see judge_errors.json)")

    with open(out_dir / "judge_config.json", "w") as f:
        json.dump({
            "judge_model": config.JUDGE_MODEL,
            "judge_effort": config.JUDGE_EFFORT,
            "max_tokens": config.JUDGE_MAX_TOKENS,
            "prompt_version": prompt_version,
            "source_generations": str((gen_dir / "generations.jsonl").relative_to(config.REPO_ROOT)),
        }, f, indent=2)

    print(f"Wrote {len(ordered)} verdicts -> {eval_path}")
    return eval_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-id", default=config.BASE_MODEL_ID)
    ap.add_argument("--prompt-version", default="v1", choices=list(PROMPTS))
    args = ap.parse_args()
    run(args.model_id, prompt_version=args.prompt_version)


if __name__ == "__main__":
    main()
