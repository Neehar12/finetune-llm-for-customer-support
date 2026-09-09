"""Render the split data into tokenized, completion-only training examples.

Uses the model's own chat template with thinking disabled and the shared
SYSTEM_PROMPT, so the training format is byte-identical to how the model is
prompted at eval/serving time. Loss is masked over the system+user prompt so
the model only learns to produce the assistant response.
"""
import json

from datasets import Dataset

import config


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def _encode_example(tokenizer, instruction, response):
    """Return (input_ids, labels) with the prompt masked to -100."""
    msgs_prompt = config.build_chat_messages(instruction)          # [system, user]
    msgs_full = msgs_prompt + [{"role": "assistant", "content": response}]

    prompt_text = tokenizer.apply_chat_template(
        msgs_prompt, tokenize=False, add_generation_prompt=True,
        enable_thinking=config.ENABLE_THINKING,
    )
    full_text = tokenizer.apply_chat_template(
        msgs_full, tokenize=False, add_generation_prompt=False,
        enable_thinking=config.ENABLE_THINKING,
    )

    prompt_ids = tokenizer(prompt_text, add_special_tokens=False).input_ids
    full_ids = tokenizer(full_text, add_special_tokens=False).input_ids

    # The rendered prompt should be a prefix of the full text; if the template
    # ever breaks that assumption, fall back to masking min(len) tokens.
    n_prompt = len(prompt_ids)
    if full_ids[:n_prompt] != prompt_ids:
        n_prompt = min(n_prompt, len(full_ids))

    labels = [-100] * n_prompt + full_ids[n_prompt:]
    input_ids = full_ids

    # Truncate from the right (rare: max real length ~660 << MAX_SEQ_LEN).
    input_ids = input_ids[: config.MAX_SEQ_LEN]
    labels = labels[: config.MAX_SEQ_LEN]
    return input_ids, labels


def build_dataset(tokenizer, path):
    rows = load_jsonl(path)
    records, truncated, no_supervision = [], 0, 0
    for r in rows:
        ids, labels = _encode_example(tokenizer, r["instruction"], r["response"])
        if len(ids) == config.MAX_SEQ_LEN:
            truncated += 1
        if all(l == -100 for l in labels):
            no_supervision += 1
            continue  # skip degenerate rows with no response tokens
        records.append({
            "input_ids": ids,
            "attention_mask": [1] * len(ids),
            "labels": labels,
        })
    print(f"  {path.name}: {len(records)} examples "
          f"(truncated at {config.MAX_SEQ_LEN}: {truncated}, dropped no-supervision: {no_supervision})")
    return Dataset.from_list(records)
