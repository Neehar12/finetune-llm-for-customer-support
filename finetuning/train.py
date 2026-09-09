"""Train Qwen3-1.7B with LoRA/QLoRA + two-tier checkpointing.

Tier 1 (in-loop, val loss): early stopping decides WHEN to stop — evaluate and
checkpoint every epoch, stop ~`EARLY_STOP_PATIENCE` epochs after val loss
plateaus, capped at `MAX_EPOCHS`.

Tier 2 (post-hoc, task metrics): we keep EVERY epoch's adapter and generate the
frozen 135-item benchmark for each, so the shipped checkpoint can be selected
locally by the Opus-5 judge (resolution -> correctness -> hallucination -> loss)
rather than by val loss alone.

Run (Kaggle notebook cell or locally with a GPU):
    python finetuning/train.py
    python finetuning/train.py --skip-eval-gen      # train only, no benchmark gen
"""
import argparse
import json

import torch
from transformers import (
    Trainer, TrainingArguments,
    DataCollatorForSeq2Seq, EarlyStoppingCallback, set_seed,
)
from peft import LoraConfig, get_peft_model

import config
import data
import generate_hf
from modeling import load_tokenizer, load_base_model


def attach_lora(model):
    lora = LoraConfig(
        r=config.LORA_R,
        lora_alpha=config.LORA_ALPHA,
        lora_dropout=config.LORA_DROPOUT,
        target_modules=config.LORA_TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()
    return model


def epoch_metrics(log_history):
    """Extract per-epoch train_loss and eval_loss from Trainer log history."""
    train_by_epoch, eval_by_epoch = {}, {}
    for e in log_history:
        ep = e.get("epoch")
        if ep is None:
            continue
        k = round(ep)
        if "loss" in e:
            train_by_epoch[k] = e["loss"]
        if "eval_loss" in e:
            eval_by_epoch[k] = e["eval_loss"]
    return train_by_epoch, eval_by_epoch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-eval-gen", action="store_true",
                    help="Train only; skip per-checkpoint benchmark generation.")
    args = ap.parse_args()

    set_seed(config.SEED)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_root = config.OUTPUT_DIR / "checkpoints"

    print(f"Method: {'QLoRA (4-bit NF4)' if config.USE_QLORA else 'LoRA (fp16)'} | "
          f"base={config.BASE_MODEL} | max_epochs={config.MAX_EPOCHS}")

    tokenizer = load_tokenizer()
    model = load_base_model(for_training=True)
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model = attach_lora(model)

    print("Tokenizing splits...")
    train_ds = data.build_dataset(tokenizer, config.TRAIN_PATH)
    val_ds = data.build_dataset(tokenizer, config.VAL_PATH)

    collator = DataCollatorForSeq2Seq(tokenizer, label_pad_token_id=-100, padding=True)

    targs = TrainingArguments(
        output_dir=str(ckpt_root),
        num_train_epochs=config.MAX_EPOCHS,
        per_device_train_batch_size=config.PER_DEVICE_BATCH,
        per_device_eval_batch_size=config.PER_DEVICE_BATCH,
        gradient_accumulation_steps=config.GRAD_ACCUM,
        learning_rate=config.LEARNING_RATE,
        lr_scheduler_type=config.LR_SCHEDULER,
        warmup_ratio=config.WARMUP_RATIO,
        weight_decay=config.WEIGHT_DECAY,
        eval_strategy=config.EVAL_STRATEGY,
        save_strategy=config.EVAL_STRATEGY,
        save_total_limit=None,               # keep every epoch for Tier-2 selection
        load_best_model_at_end=True,
        metric_for_best_model=config.METRIC_FOR_BEST,
        greater_is_better=False,
        logging_steps=20,
        fp16=config.FP16,
        bf16=config.BF16,
        seed=config.SEED,
        report_to="none",
        gradient_checkpointing=True,
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        callbacks=[EarlyStoppingCallback(
            early_stopping_patience=config.EARLY_STOP_PATIENCE,
            early_stopping_threshold=config.EARLY_STOP_THRESHOLD,
        )],
    )

    trainer.train()

    # Save the best-by-loss adapter (Trainer restored it via load_best_model_at_end).
    best_dir = config.OUTPUT_DIR / "best_adapter"
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    print(f"Saved best-by-loss adapter -> {best_dir}")

    train_by_epoch, eval_by_epoch = epoch_metrics(trainer.state.log_history)

    manifest = {
        "base_model": config.BASE_MODEL,
        "method": "qlora" if config.USE_QLORA else "lora",
        "seed": config.SEED,
        "max_epochs": config.MAX_EPOCHS,
        "early_stop_patience": config.EARLY_STOP_PATIENCE,
        "lora": {"r": config.LORA_R, "alpha": config.LORA_ALPHA,
                 "dropout": config.LORA_DROPOUT, "targets": config.LORA_TARGET_MODULES},
        "max_seq_len": config.MAX_SEQ_LEN,
        "learning_rate": config.LEARNING_RATE,
        "effective_batch": config.PER_DEVICE_BATCH * config.GRAD_ACCUM,
        "best_by_loss_checkpoint": trainer.state.best_model_checkpoint,
        "epochs": [],
    }

    # Base reference (NO adapter), generated through the SAME fp16 HF path as the
    # epoch checkpoints, so per-epoch selection deltas aren't confounded by the
    # Ollama-vs-fp16 runtime difference. (The Ollama Q4_K_M base stays the
    # reference for the FINAL comparison.)
    if not args.skip_eval_gen:
        print("[base] generating benchmark from base model (no adapter)")
        base0 = load_base_model(for_training=False)
        base_gen = config.OUTPUT_DIR / "base_fp16" / "generations.jsonl"
        generate_hf.generate_over_benchmark(
            base0, tokenizer, config.BENCHMARK_PATH, base_gen,
            model_id=f"{config.MODEL_ID}-base-fp16",
        )
        manifest["base_fp16"] = {"generations": str(base_gen)}
        del base0
        torch.cuda.empty_cache()

    # Tier 2: generate the frozen benchmark for every saved checkpoint (fp16),
    # so each epoch can be judged locally for task-metric selection.
    ckpts = sorted(ckpt_root.glob("checkpoint-*"),
                   key=lambda p: int(p.name.split("-")[1]))
    for k, ckpt in enumerate(ckpts, 1):
        rec = {
            "epoch": k,
            "checkpoint_dir": str(ckpt),
            "train_loss": train_by_epoch.get(k),
            "eval_loss": eval_by_epoch.get(k),
        }
        if not args.skip_eval_gen:
            from peft import PeftModel
            base = load_base_model(for_training=False)
            merged = PeftModel.from_pretrained(base, str(ckpt))
            gen_path = config.OUTPUT_DIR / f"epoch_{k}" / "generations.jsonl"
            print(f"[epoch {k}] generating benchmark from {ckpt.name} (eval_loss={rec['eval_loss']})")
            generate_hf.generate_over_benchmark(
                merged, tokenizer, config.BENCHMARK_PATH, gen_path,
                model_id=f"{config.MODEL_ID}-epoch{k}",
            )
            rec["generations"] = str(gen_path)
            del merged, base
            torch.cuda.empty_cache()
        manifest["epochs"].append(rec)

    with open(config.OUTPUT_DIR / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    with open(config.OUTPUT_DIR / "training_metrics.json", "w") as f:
        json.dump({"train_loss_by_epoch": train_by_epoch,
                   "eval_loss_by_epoch": eval_by_epoch,
                   "log_history": trainer.state.log_history}, f, indent=2)
    print(f"\nDone. Outputs in {config.OUTPUT_DIR}")
    print("Next: download outputs; judge each epoch's generations locally with "
          "evaluation/judge.py --prompt-version v2, then select the best epoch.")


if __name__ == "__main__":
    main()
