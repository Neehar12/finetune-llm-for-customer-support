# Fine-tuning (Task 2)

Fine-tunes **Qwen3-1.7B** on the cleaned Bitext train split with **LoRA (fp16)**
by default (**QLoRA** is a one-flag fallback), on a free **Kaggle T4**.

## Design

- **Prompt contract reused** from `../common/prompting.py` — examples are rendered
  with Qwen3's chat template, **thinking disabled**, and the same system prompt used
  at eval/serving. **Completion-only loss** (system+user prompt masked).
- **Two-tier checkpointing:**
  - *Tier 1 — when to stop:* evaluate + checkpoint every epoch; `EarlyStoppingCallback`
    on **val loss** (patience 2), capped at `MAX_EPOCHS=6`. `load_best_model_at_end`.
  - *Tier 2 — what to ship:* keep **every** epoch's adapter and generate the frozen
    135-item benchmark for each (fp16). Final checkpoint is chosen locally by the
    Opus-5 v2 judge (resolution → correctness → hallucination → val loss), not by
    val loss alone (per `../finetuning_evaluation_implementation_guide.md` §15).
- **Quant consistency (Option A):** checkpoint *selection* uses fp16 HF generation
  (fine — it only picks an epoch). The final base-vs-tuned headline runs *both*
  models as **Q4_K_M GGUF via Ollama**.

## Hyperparameters (`config.py`)

| | value |
|---|---|
| base | `Qwen/Qwen3-1.7B` |
| method | LoRA fp16 (`USE_QLORA=False`) |
| LoRA r / α / dropout | 16 / 32 / 0.05 |
| target modules | q,k,v,o,gate,up,down proj |
| max_seq_len | 1024 (longest example ~660 tok) |
| max_epochs / early-stop patience | 6 / 2 |
| lr / schedule / warmup | 2e-4 / cosine / 3% |
| effective batch | 32 (8 × grad-accum 4) |
| precision | fp16 (T4) |

To use QLoRA instead: set `USE_QLORA = True` in `config.py`.

## Run on Kaggle

New notebook → **Accelerator: GPU T4** → **Internet: ON**. Then:

```python
# 1. Get the code (or upload the repo as a Kaggle dataset and adjust paths)
!git clone https://github.com/<you>/finetune-llm-for-customer-support.git
%cd finetune-llm-for-customer-support

# 2. Install training deps
!pip install -q -r finetuning/requirements.txt

# 3. Train (downloads Qwen3-1.7B from HF; logs train/val loss per epoch,
#    saves an adapter + benchmark generations per epoch)
!python finetuning/train.py

# 4. Package outputs for download
!cd /kaggle/working && zip -r outputs.zip outputs
```

Download `outputs.zip` from the Kaggle output panel. It contains:

```
outputs/
  checkpoints/checkpoint-*/     # per-epoch LoRA adapters (all kept)
  best_adapter/                 # best-by-val-loss adapter
  base_fp16/generations.jsonl   # BASE model (no adapter), same fp16 path -> matched reference
  epoch_1/generations.jsonl     # frozen-benchmark answers per epoch (fp16)
  epoch_2/generations.jsonl
  ...
  training_metrics.json         # train/val loss per epoch + full log history
  run_manifest.json             # config + per-epoch checkpoint/loss/gen index
```

`base_fp16/` is the base model's answers generated through the **same fp16 HF
path** (no adapter) as the epochs — so per-epoch selection deltas aren't
confounded by the Ollama-vs-fp16 difference. (The Ollama Q4_K_M base benchmark
stays the reference for the **final** comparison.) `train.py` produces it
automatically; to grab it early in its own cell:

```python
!python finetuning/generate_base.py     # writes outputs/base_fp16/generations.jsonl
```

## Select the checkpoint (locally)

```bash
unzip outputs.zip -d finetuning/            # -> finetuning/outputs/
export ANTHROPIC_API_KEY=...  ANTHROPIC_WORKSPACE_ID=...
python3 finetuning/select_checkpoint.py --outputs finetuning/outputs
```

This judges the fp16 base reference and each epoch's generations with the Opus-5
v2 rubric, prints a ranked table with **Δ-vs-fp16-base** columns, and names the
epoch to ship. Verdicts land in `evaluation/experiments/qwen3-1.7b-lora-*-judge-v2/`.

## Next (serving + final eval — Task 4)

Merge the selected epoch's adapter into the fp16 base → convert to GGUF →
quantize **Q4_K_M** → load into Ollama. Re-baseline the base through the same
conversion, then run the final **base-vs-tuned comparison on the untouched TEST
split**, both as Q4_K_M via the `evaluation/` harness with `--prompt-version v2`.
