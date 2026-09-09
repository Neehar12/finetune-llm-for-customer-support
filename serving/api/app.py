"""Customer-support HTTP API — thin wrapper over Ollama.

Serves the fine-tuned model (default `cs-tuned`) behind a clean endpoint that
bakes in the FROZEN prompt contract from `common/prompting.py` (system prompt,
no-think, greedy/seed). Callers send only the customer message; the exact
train==serve template is applied server-side.

Run:
    MODEL_TAG=cs-tuned uvicorn app:app --host 0.0.0.0 --port 8000
    # from repo root: uvicorn serving.api.app:app ...

Endpoints:
    GET  /health           -> {status, model}
    POST /chat  {message}   -> {response, model, timing}
    POST /compare {message} -> {base, tuned}   (side-by-side, for the demo)
"""
import os
import re
import sys
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import ollama

# import the frozen contract (repo root = two levels up from serving/api/)
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from common.prompting import build_chat_messages, GEN_OPTIONS, THINK, SYSTEM_PROMPT  # noqa: E402

MODEL_TAG = os.environ.get("MODEL_TAG", "cs-tuned")
BASE_TAG = os.environ.get("BASE_TAG", "cs-base")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_THINK_RE = re.compile(r"^\s*<think>.*?</think>\s*", re.DOTALL)

client = ollama.Client(host=OLLAMA_HOST)
app = FastAPI(title="Customer Support Assistant", version="1.0")


class ChatIn(BaseModel):
    message: str


def _generate(model_tag: str, message: str) -> dict:
    messages = build_chat_messages(message)
    t0 = time.perf_counter()
    try:
        resp = client.chat(model=model_tag, messages=messages,
                           options=GEN_OPTIONS, think=THINK)
    except TypeError:  # older ollama client without `think`
        resp = client.chat(model=model_tag, messages=messages, options=GEN_OPTIONS)
    wall_ms = (time.perf_counter() - t0) * 1000
    text = _THINK_RE.sub("", resp["message"]["content"]).strip()
    # Ollama returns nanosecond timings; surface a well-defined subset.
    ns = lambda k: resp.get(k) or 0
    eval_count, eval_dur = ns("eval_count"), ns("eval_duration")
    timing = {
        "wall_ms": round(wall_ms, 1),
        "output_tokens": eval_count,
        "decode_tokens_per_s": round(eval_count / (eval_dur / 1e9), 1) if eval_dur else None,
        "prompt_tokens": ns("prompt_eval_count"),
        "total_ms": round(ns("total_duration") / 1e6, 1),
        "load_ms": round(ns("load_duration") / 1e6, 1),
    }
    return {"response": text, "model": model_tag, "timing": timing}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_TAG, "system_prompt": SYSTEM_PROMPT}


@app.post("/chat")
def chat(body: ChatIn):
    return _generate(MODEL_TAG, body.message)


@app.post("/compare")
def compare(body: ChatIn):
    return {"base": _generate(BASE_TAG, body.message),
            "tuned": _generate(MODEL_TAG, body.message)}
