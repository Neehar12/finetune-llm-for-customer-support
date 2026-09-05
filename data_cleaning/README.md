# Data cleaning & leakage-aware splitting

Prepares the Bitext customer-support dataset for fine-tuning by building
**train / validation / test** splits that don't leak paraphrases across the boundary.

## Why this matters

Bitext is paraphrase-generated: each of the 27 intents has hundreds of near-identical
instructions. A **random row split** puts paraphrase siblings on both sides of the split,
so test scores measure memorisation, not generalisation. We instead cluster paraphrases
into groups and assign **whole groups** to a single split.

## Run

```bash
pip install -r requirements.txt

python prepare_splits.py \
  --csv Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv \
  --out data/splits \
  --test-size 1000 --val-size 500
```

Optional semantic-paraphrase clustering (also catches low-lexical-overlap paraphrases):

```bash
python prepare_splits.py --csv <csv> --out data/splits --embed-model all-MiniLM-L6-v2
```

## Pipeline (`prepare_splits.py`)

1. **Normalise** instructions — lowercase, strip `{{placeholders}}` and punctuation.
2. **Exact dedupe** on `(intent, instruction_norm, response_norm)`. The same instruction
   with a *different* valid response is kept as legitimate training signal.
3. **Paraphrase grouping** — per intent, average-linkage agglomerative clustering on
   char n-gram (3–5) TF-IDF cosine. Whole groups become the unit of splitting.
4. **Group-aware, intent-stratified split** — each group goes wholesale to one split;
   per-intent targets keep all 27 intents represented in val/test.
5. **Leakage report** — max TF-IDF cosine of each test instruction to any train
   instruction, group-aware vs. a naive random baseline.

## Outputs (`data/splits/`)

- `train.jsonl`, `val.jsonl`, `test.jsonl` — one record per line, original columns + `group`.
- `split_report.md` — split sizes, per-intent test coverage, leakage table.

## Result (seed 42, TF-IDF, test=1000 / val=500)

| split strategy | mean max sim | ≥0.8 | ≥0.9 | exact (=1.0) |
|---|---|---|---|---|
| random rows    | 0.769 | 44.2% | 22.5% | **17.5%** |
| group-aware    | 0.611 | 10.0% |  1.1% |  **0.0%** |

A naive random split makes **17.5% of test rows exact copies of a training row**. The
group-aware split drops that to **0%**, so reported base-vs-fine-tuned gains reflect real
generalisation. Final sizes: train 25,173 / val 598 / test 1,100 (whole-group assignment
overshoots the 1000/500 targets slightly); all 27 intents present in test (36–54 rows each).

### Notes

- Dataset is 26,872 rows, 27 intents, **11** categories (the brief says 10).
- Only **1** exact `(instruction, response)` duplicate exists; the real leakage risk is
  near-duplicate paraphrases, which is what the grouping addresses.
- The `flags` column encodes linguistic-style tags of the *instruction* (register,
  colloquialisms, typos); it is metadata, not response-training signal.
