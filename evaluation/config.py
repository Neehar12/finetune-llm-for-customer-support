"""Paths and knobs for the evaluation task.

The model-facing contract (system prompt, chat format, generation settings)
lives in `common/prompting.py` and is imported here so there is one source of
truth. This file only holds evaluation-specific configuration.
"""
import sys
from pathlib import Path

# Make the repo root importable so `common` resolves regardless of CWD.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from common.prompting import SYSTEM_PROMPT, THINK, GEN_OPTIONS, build_chat_messages  # noqa: E402,F401

# --- Data splits (produced by the data_cleaning task) ----------------------
SPLITS_DIR = REPO_ROOT / "data_cleaning" / "data" / "splits"
VAL_PATH = SPLITS_DIR / "val.jsonl"
TEST_PATH = SPLITS_DIR / "test.jsonl"

# --- Evaluation artifacts --------------------------------------------------
EVAL_DIR = Path(__file__).resolve().parent
BENCH_DIR = EVAL_DIR / "data" / "benchmark"
BENCH_PATH = BENCH_DIR / "val_benchmark.jsonl"
BENCH_META_PATH = BENCH_DIR / "benchmark_meta.json"
EXPERIMENTS_DIR = EVAL_DIR / "experiments"

# --- Benchmark construction (Phase 2) --------------------------------------
SEED = 42
PER_INTENT = 5  # 5 x 27 intents = 135 frozen benchmark items

# --- Base model under test (served locally via Ollama) ---------------------
BASE_MODEL_TAG = "qwen3:1.7b"        # Ollama tag
BASE_MODEL_ID = "qwen3-1.7b-base"    # label used for the experiment directory
OLLAMA_HOST = "http://localhost:11434"

# --- LLM-as-a-judge --------------------------------------------------------
JUDGE_MODEL = "claude-opus-5"
JUDGE_MAX_TOKENS = 4096   # room for adaptive thinking + the JSON verdict
JUDGE_EFFORT = "medium"   # calibration vs cost/latency tradeoff
JUDGE_WORKERS = 8         # parallel judge calls
