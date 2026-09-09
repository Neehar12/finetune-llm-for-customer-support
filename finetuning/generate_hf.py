"""HF/transformers generation over the frozen benchmark.

Mirrors `evaluation/generate.py` (the Ollama path) but runs a Hugging Face model
directly, so we can score training checkpoints on Kaggle without exporting each
one to GGUF. Uses the same prompt contract and deterministic (greedy) decoding,
and writes `generations.jsonl` in the exact schema `evaluation/judge.py` expects.

This is used for CHECKPOINT SELECTION only (fp16). The final base-vs-tuned
headline is run through the Q4_K_M GGUF / Ollama path for both models.
"""
import json
import re

import torch

import config

_THINK_RE = re.compile(r"^\s*<think>.*?</think>\s*", re.DOTALL)


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def strip_think(text):
    return _THINK_RE.sub("", text).strip()


@torch.no_grad()
def generate_over_benchmark(model, tokenizer, benchmark_path, out_path, model_id,
                            model_tag="hf-fp16"):
    items = load_jsonl(benchmark_path)
    model.eval()
    device = next(model.parameters()).device
    max_new = config.GEN_OPTIONS["num_predict"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for i, it in enumerate(items, 1):
            prompt = tokenizer.apply_chat_template(
                config.build_chat_messages(it["instruction"]),
                tokenize=False, add_generation_prompt=True,
                enable_thinking=config.ENABLE_THINKING,
            )
            enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(device)
            out = model.generate(
                **enc,
                max_new_tokens=max_new,
                do_sample=False,               # greedy, deterministic
                temperature=None, top_p=None, top_k=None,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
            gen_ids = out[0][enc["input_ids"].shape[1]:]
            text = strip_think(tokenizer.decode(gen_ids, skip_special_tokens=True))
            f.write(json.dumps({
                "id": it["id"],
                "intent": it["intent"],
                "category": it["category"],
                "instruction": it["instruction"],
                "reference_response": it["reference_response"],
                "generated_response": text,
                "model_id": model_id,
                "model_tag": model_tag,
            }, ensure_ascii=False) + "\n")
            if i % 25 == 0 or i == len(items):
                print(f"    generated {i}/{len(items)}")
    print(f"  wrote generations -> {out_path}")
