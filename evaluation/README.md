# Evaluation

Task-level, leakage-free evaluation of the customer-support model, following
`../finetuning_evaluation_implementation_guide.md`. Same harness is used for the
base-model baseline (now), per-checkpoint eval during fine-tuning, and the final
held-out test comparison.

## What "better" means

We score every answer on the guide's five dimensions with an **LLM judge**
(Claude Opus 5), not on wording overlap (BLEU/ROUGE), because a support reply can
be correct and helpful while phrased nothing like the reference:

| Metric | Scale | Question |
|---|---|---|
| issue_understanding | 1–5 | Did it understand what the customer needs? |
| correctness | 1–5 | Is the information correct? |
| resolution_quality | 1–5 | Does it resolve the issue / give correct next steps? |
| hallucination | bool | Did it invent unsupported facts/policies? |
| support_quality | 1–5 | Clear, professional, appropriately concise? |

Checkpoint selection priority (per the guide): resolution_quality → correctness →
hallucination rate → validation loss.

## Design choices

- **Benchmark = validation only.** 135 items, 5 per intent × 27 intents
  (`build_benchmark.py`), frozen with seed 42. The held-out **test** split is
  untouched until the final base-vs-tuned comparison.
- **Frozen prompt contract.** System prompt, chat format, and generation
  settings live in `../common/prompting.py` and are imported by eval, and later
  by training and serving — one source of truth, so the prompt template is
  identical everywhere (a graded requirement).
- **Fair comparison.** Base and fine-tuned models use the same benchmark, system
  prompt, generation settings (`temperature=0`, `seed=42`, `num_predict=512`),
  and the same frozen judge prompt. Only the weights differ.
- **Qwen3 thinking off.** Direct replies, predictable latency; matches the
  direct-style training targets.
- **Placeholders.** Reference responses contain `{{...}}` template variables; the
  judge is told to treat them as variables, not to penalize or flag them.

## Layout

```
common/prompting.py           # frozen prompt + generation contract (repo root)
evaluation/
  config.py                   # paths + knobs
  prompts.py                  # frozen judge rubric/prompt
  build_benchmark.py          # Phase 2: freeze val benchmark
  generate.py                 # run an Ollama model over the benchmark
  judge.py                    # score with Claude Opus 5 (structured JSON)
  aggregate.py                # summary + per-category / per-intent metrics
  run_base_benchmark.py       # Phase 3: base baseline, end to end
  data/benchmark/             # val_benchmark.jsonl (frozen) + meta
  experiments/<model_id>/     # generations, per-example verdicts, aggregate
```

## Run

```bash
pip install -r requirements.txt          # ollama + anthropic clients
# base model must be pulled in Ollama:  ollama pull qwen3:1.7b
export ANTHROPIC_API_KEY=sk-ant-...       # judge = Claude Opus 5

python run_base_benchmark.py              # build → generate → judge → aggregate
```

Outputs land in `experiments/qwen3-1.7b-base/`:
`generations.jsonl`, `evaluation_results.jsonl` (per-example scores + reasons),
`aggregate_metrics.json` (means, hallucination rate, per-category/intent).

Re-run a single stage against an existing experiment:

```bash
python generate.py --model-tag qwen3:1.7b --model-id qwen3-1.7b-base
python judge.py    --model-id qwen3-1.7b-base
python aggregate.py --model-id qwen3-1.7b-base
```

Later, the fine-tuned model reuses the same commands with a different
`--model-tag` / `--model-id`.
