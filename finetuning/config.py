"""Fine-tuning configuration (Task 2).

Trains Qwen3-1.7B on the cleaned Bitext train split with LoRA (default) or
QLoRA (one flag). The model-facing prompt/generation contract is imported from
`common/prompting.py`, so training renders examples exactly the way the model
is prompted at eval and serving time (train == eval == serve).

Compute target: Kaggle T4 (16 GB) → fp16 (Turing has no bf16).
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from common.prompting import (  # noqa: E402,F401
    SYSTEM_PROMPT, THINK, GEN_OPTIONS, build_chat_messages,
)

# --- Base model ------------------------------------------------------------
BASE_MODEL = "Qwen/Qwen3-1.7B"          # HF checkpoint we fine-tune
ENABLE_THINKING = THINK                  # False — direct replies, matches eval/serve

# --- Method: LoRA (default) vs QLoRA (memory-saving fallback) ---------------
# LoRA keeps the base in fp16 during training (fits T4 easily at 1.7B) and
# avoids the NF4->merge mismatch. Flip to True for 4-bit QLoRA if VRAM-bound.
USE_QLORA = False

# --- LoRA hyperparameters --------------------------------------------------
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",   # attention
    "gate_proj", "up_proj", "down_proj",      # MLP
]

# --- Sequence length -------------------------------------------------------
# Longest instruction+response ~660 tokens incl. system prompt; 1024 => no truncation.
MAX_SEQ_LEN = 1024

# --- Training --------------------------------------------------------------
MAX_EPOCHS = 3              # val loss plateaus by ~epoch 2-3 on this templated data;
                           # cap at 3 to avoid overfit and fit free-compute time budget.
                           # Early stopping (patience 2) can still stop sooner.
LEARNING_RATE = 2e-4
LR_SCHEDULER = "cosine"
WARMUP_RATIO = 0.03
WEIGHT_DECAY = 0.0
PER_DEVICE_BATCH = 8
GRAD_ACCUM = 4             # effective batch ~32
SEED = 42
FP16 = True               # T4 = fp16 (set False + BF16 True on Ampere+)
BF16 = False

# --- Early stopping (Tier 1: decides WHEN to stop, on val loss) ------------
EVAL_STRATEGY = "epoch"        # eval + checkpoint every epoch
EARLY_STOP_PATIENCE = 2        # stop ~2 evals after val loss plateaus
EARLY_STOP_THRESHOLD = 0.0     # min improvement to count
METRIC_FOR_BEST = "eval_loss"  # in-loop metric only; task metrics decide the ship (Tier 2)

# --- Data / paths ----------------------------------------------------------
SPLITS_DIR = REPO_ROOT / "data_cleaning" / "data" / "splits"
TRAIN_PATH = SPLITS_DIR / "train.jsonl"
VAL_PATH = SPLITS_DIR / "val.jsonl"
BENCHMARK_PATH = REPO_ROOT / "evaluation" / "data" / "benchmark" / "val_benchmark.jsonl"

# Output dir: /kaggle/working on Kaggle, else finetuning/outputs locally.
_KAGGLE = Path("/kaggle/working")
OUTPUT_DIR = Path(os.environ.get(
    "FT_OUTPUT_DIR",
    str(_KAGGLE / "outputs") if _KAGGLE.exists() else str(Path(__file__).resolve().parent / "outputs"),
))

MODEL_ID = "qwen3-1.7b-lora"   # label for downstream eval experiment dirs
