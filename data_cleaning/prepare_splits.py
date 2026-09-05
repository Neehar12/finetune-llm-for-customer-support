"""
Leakage-aware train / validation / test split for the Bitext customer-support dataset.

Why this exists
---------------
Bitext is paraphrase-generated: each of the 27 intents has hundreds of near-identical
instructions. A random row split puts paraphrase siblings on both sides, so test scores
overstate generalisation. This script:

  1. normalises instructions (lowercase, strip {{placeholders}} and punctuation)
  2. drops exact (instruction, response) duplicates — same instruction with a different
     response is kept
  3. within each intent, clusters near-duplicate instructions into "paraphrase groups"
     (average-linkage agglomerative on char n-gram TF-IDF cosine, or on sentence
     embeddings with --embed-model)
  4. assigns whole groups to train / val / test, stratified by intent
  5. writes a leakage report: for every test row, the max similarity to any training row,
     compared against a naive random split as the baseline

Usage
-----
    python prepare_splits.py --csv path/to/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv \
        --out data/splits --test-size 1000 --val-size 500

Outputs
-------
    <out>/train.jsonl, val.jsonl, test.jsonl   one record per line, original columns preserved
    <out>/split_report.md                        stats + leakage analysis
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering

PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")
NON_ALNUM = re.compile(r"[^a-z0-9\s]")
WS = re.compile(r"\s+")


# --------------------------------------------------------------------------- #
# 1. Normalisation + exact dedupe
# --------------------------------------------------------------------------- #
def normalise(text: str) -> str:
    text = text.lower()
    text = PLACEHOLDER.sub(" ", text)
    text = NON_ALNUM.sub(" ", text)
    return WS.sub(" ", text).strip()


def load_and_dedupe(csv_path: Path) -> tuple[pd.DataFrame, int]:
    df = pd.read_csv(csv_path)
    required = {"flags", "instruction", "category", "intent", "response"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df = df.dropna(subset=["instruction", "response"]).copy()
    df["instruction_norm"] = df["instruction"].map(normalise)
    df["response_norm"] = df["response"].map(normalise)
    before = len(df)
    # Dedupe on the (instruction, response) PAIR. The same instruction with a different
    # valid response is legitimate training signal and is kept; identical instructions
    # still land in the same paraphrase group, so they can never straddle train/test.
    df = df.drop_duplicates(subset=["intent", "instruction_norm", "response_norm"]).reset_index(drop=True)
    return df, before - len(df)


# --------------------------------------------------------------------------- #
# 2. Paraphrase grouping within each intent
# --------------------------------------------------------------------------- #
def _embed(texts: list[str], model_name: str) -> np.ndarray:
    """Sentence embeddings (L2-normalised) so cosine == dot product."""
    from sentence_transformers import SentenceTransformer  # optional dependency

    model = SentenceTransformer(model_name)
    return model.encode(texts, batch_size=256, normalize_embeddings=True, show_progress_bar=False)


def paraphrase_groups(texts: list[str], threshold: float, emb: np.ndarray | None = None) -> np.ndarray:
    """Return a group id per text.

    Average-linkage agglomerative clustering on TF-IDF cosine distance: two clusters merge
    only if their *average* pairwise similarity is >= threshold. (Single-linkage / connected
    components chains every paraphrase in an intent into one giant blob, which is useless
    for splitting.)"""
    n = len(texts)
    if n == 1:
        return np.zeros(1, dtype=int)

    # Character n-grams so typo / colloquial variants ("cancle", "u") still land near
    # their clean siblings.
    if emb is not None:
        dist = 1.0 - emb @ emb.T
    else:
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        X = vec.fit_transform(texts)
        dist = 1.0 - (X @ X.T).toarray()
    np.fill_diagonal(dist, 0.0)
    dist = np.clip(dist, 0.0, 1.0)

    clus = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="average",
        distance_threshold=1.0 - threshold,
    )
    return clus.fit_predict(dist)


def assign_groups(df: pd.DataFrame, threshold: float, embed_model: str | None = None) -> pd.DataFrame:
    df = df.copy()
    df["group"] = -1
    all_emb = _embed(df["instruction_norm"].tolist(), embed_model) if embed_model else None
    offset = 0
    for intent, sub in df.groupby("intent", sort=False):
        emb = all_emb[df.index.get_indexer(sub.index)] if all_emb is not None else None
        labels = paraphrase_groups(sub["instruction_norm"].tolist(), threshold, emb)
        df.loc[sub.index, "group"] = labels + offset
        offset += labels.max() + 1
    return df


# --------------------------------------------------------------------------- #
# 3. Group-aware, intent-stratified split
# --------------------------------------------------------------------------- #
def group_split(
    df: pd.DataFrame, test_size: int, val_size: int, seed: int
) -> pd.DataFrame:
    """Assign each paraphrase group wholesale to train/val/test. Per intent, we aim for the
    same proportion of rows in val/test as the global target."""
    rng = np.random.default_rng(seed)
    n = len(df)
    test_frac, val_frac = test_size / n, val_size / n
    df = df.copy()
    df["split"] = "train"

    for intent, sub in df.groupby("intent", sort=False):
        target_test = int(round(len(sub) * test_frac))
        target_val = int(round(len(sub) * val_frac))

        groups = sub.groupby("group").size()
        order = rng.permutation(groups.index.values)

        test_n = val_n = 0
        for g in order:
            size = groups[g]
            mask = df.index[(df["intent"] == intent) & (df["group"] == g)]
            # Fill test, then val. A group that would overshoot its target by >50% is left
            # in train so one giant paraphrase cluster cannot swallow the eval set.
            if test_n < target_test and test_n + size <= 1.5 * target_test:
                df.loc[mask, "split"] = "test"
                test_n += size
            elif val_n < target_val and val_n + size <= 1.5 * target_val:
                df.loc[mask, "split"] = "val"
                val_n += size
            if test_n >= target_test and val_n >= target_val:
                break

    counts = Counter(df["split"])
    for name in ("train", "val", "test"):
        if counts.get(name, 0) == 0:
            raise RuntimeError(
                f"Split '{name}' is empty. Lower --threshold (groups too coarse) or "
                f"reduce --test-size/--val-size."
            )
    return df


def random_split(df: pd.DataFrame, test_size: int, seed: int) -> pd.Series:
    """Naive row-level random split, used only as the leakage baseline."""
    rng = np.random.default_rng(seed)
    split = pd.Series("train", index=df.index)
    split.loc[rng.choice(df.index.values, size=test_size, replace=False)] = "test"
    return split


# --------------------------------------------------------------------------- #
# 4. Leakage analysis
# --------------------------------------------------------------------------- #
def max_sim_to_train(df: pd.DataFrame, split: pd.Series, emb: np.ndarray | None = None) -> np.ndarray:
    """Max TF-IDF cosine similarity from each test row to any train row of the same intent.
    Returns one value per test row (in df order)."""
    out = np.zeros(len(df))
    for intent, sub in df.groupby("intent", sort=False):
        tr = sub.index[split.loc[sub.index] == "train"]
        te = sub.index[split.loc[sub.index] == "test"]
        if len(tr) == 0 or len(te) == 0:
            continue
        if emb is not None:
            sims = emb[df.index.get_indexer(te)] @ emb[df.index.get_indexer(tr)].T
        else:
            vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(
                df.loc[sub.index, "instruction_norm"]
            )
            Xtr = vec.transform(df.loc[tr, "instruction_norm"])
            Xte = vec.transform(df.loc[te, "instruction_norm"])
            sims = (Xte @ Xtr.T).toarray()
        out[df.index.get_indexer(te)] = sims.max(axis=1)
    return out[(split == "test").values]


def leakage_stats(sims: np.ndarray) -> dict:
    return {
        "n": int(len(sims)),
        "mean_max_sim": float(sims.mean()) if len(sims) else 0.0,
        "frac_over_0.9": float((sims >= 0.9).mean()) if len(sims) else 0.0,
        "frac_over_0.8": float((sims >= 0.8).mean()) if len(sims) else 0.0,
        "frac_exact_1.0": float((sims >= 0.999).mean()) if len(sims) else 0.0,
    }


# --------------------------------------------------------------------------- #
# 5. Report + write
# --------------------------------------------------------------------------- #
def write_outputs(df: pd.DataFrame, out: Path, report: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cols = ["flags", "instruction", "category", "intent", "response", "group"]
    for name in ("train", "val", "test"):
        sub = df[df["split"] == name][cols]
        with (out / f"{name}.jsonl").open("w") as f:
            for rec in sub.to_dict(orient="records"):
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    lines = ["# Split report", ""]
    lines.append(f"- Rows after NA drop: {report['rows_raw']}")
    lines.append(f"- Exact duplicates removed (intent + normalised instruction + normalised response): {report['dupes_removed']}")
    lines.append(f"- Rows used: {report['rows_used']}")
    lines.append(f"- Paraphrase groups: {report['n_groups']} (threshold {report['threshold']}, similarity: {report['similarity']})")
    lines.append(f"- Largest group size: {report['largest_group']}")
    lines.append("")
    lines.append("## Split sizes")
    for k, v in report["split_sizes"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Intent coverage in test (rows per intent)")
    for k, v in sorted(report["test_by_intent"].items()):
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Leakage: max TF-IDF cosine of each test instruction to any train instruction")
    lines.append("")
    lines.append("| split strategy | mean max sim | >=0.8 | >=0.9 | exact |")
    lines.append("|---|---|---|---|---|")
    for name in ("random_rows", "group_aware"):
        s = report["leakage"][name]
        lines.append(
            f"| {name} | {s['mean_max_sim']:.3f} | {s['frac_over_0.8']:.1%} | "
            f"{s['frac_over_0.9']:.1%} | {s['frac_exact_1.0']:.1%} |"
        )
    lines.append("")
    lines.append(
        "Group-aware numbers will not be zero: paraphrases within an intent share vocabulary by "
        "construction. The point is the drop relative to the random baseline."
    )
    (out / "split_report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--out", default=Path("data/splits"), type=Path)
    ap.add_argument("--test-size", default=1000, type=int)
    ap.add_argument("--val-size", default=500, type=int)
    ap.add_argument("--threshold", default=0.6, type=float,
                    help="average within-group TF-IDF cosine required to merge paraphrase groups (0.4-0.6 is sane)")
    ap.add_argument("--seed", default=42, type=int)
    ap.add_argument("--embed-model", default=None,
                    help="Optional sentence-transformers model (e.g. all-MiniLM-L6-v2). If set, "
                         "clustering and the leakage check use embeddings instead of TF-IDF, "
                         "which also catches semantic paraphrases with little lexical overlap.")
    args = ap.parse_args()

    df, dupes = load_and_dedupe(args.csv)
    rows_raw = len(df) + dupes

    df = assign_groups(df, args.threshold, args.embed_model)
    emb = _embed(df["instruction_norm"].tolist(), args.embed_model) if args.embed_model else None
    group_sizes = df.groupby("group").size()

    df = group_split(df, args.test_size, args.val_size, args.seed)

    naive = random_split(df, args.test_size, args.seed)
    leak_random = leakage_stats(max_sim_to_train(df, naive, emb))
    leak_group = leakage_stats(max_sim_to_train(df, df["split"], emb))

    report = {
        "rows_raw": rows_raw,
        "dupes_removed": dupes,
        "rows_used": len(df),
        "threshold": args.threshold,
        "similarity": args.embed_model or "tfidf",
        "n_groups": int(df["group"].nunique()),
        "largest_group": int(group_sizes.max()),
        "split_sizes": dict(Counter(df["split"])),
        "test_by_intent": dict(Counter(df[df["split"] == "test"]["intent"])),
        "leakage": {"random_rows": leak_random, "group_aware": leak_group},
    }
    write_outputs(df, args.out, report)

    print(json.dumps(report, indent=2))
    print(f"\nWrote {args.out}/train.jsonl, val.jsonl, test.jsonl, split_report.md")


if __name__ == "__main__":
    main()
