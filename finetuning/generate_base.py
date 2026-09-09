"""Generate the frozen-benchmark answers for the BASE model (no adapter), fp16.

Standalone so you can grab the fp16 base reference in a quick Kaggle cell before
committing to a full training run. Uses the identical loader + prompt contract +
greedy decoding as the per-epoch checkpoint generation, so the base and the
tuned epochs are compared on the exact same fp16 HF path during selection.

(The Ollama Q4_K_M base benchmark remains the reference for the FINAL comparison.)

Run (Kaggle GPU cell, or any machine with a GPU):
    python finetuning/generate_base.py
"""
import torch

import config
import generate_hf
import modeling


def main():
    tok = modeling.load_tokenizer()
    model = modeling.load_base_model(for_training=False)
    out_path = config.OUTPUT_DIR / "base_fp16" / "generations.jsonl"
    print(f"Generating base ({config.BASE_MODEL}, "
          f"{'4-bit' if config.USE_QLORA else 'fp16'}) over the frozen benchmark...")
    generate_hf.generate_over_benchmark(
        model, tok, config.BENCHMARK_PATH, out_path,
        model_id=f"{config.MODEL_ID}-base-fp16",
    )
    del model
    torch.cuda.empty_cache()
    print(f"Base reference generations -> {out_path}")


if __name__ == "__main__":
    main()
