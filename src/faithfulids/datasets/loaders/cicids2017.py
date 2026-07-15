"""Real CICIDS2017 loader (L1).

Reads the CICIDS2017 CSVs as distributed (or an upstream-corrected variant) from
a directory — on Kaggle this is a mounted dataset. Performs the minimal,
uncontroversial cleaning a *pilot* needs (strip column names, drop flow-identity
/ timestamp leakage columns, coerce features numeric, drop NaN/Inf rows, derive
``attack_class``, binary ``label``, and the coarsened multi-class ``target_class``
— see ``CANONICAL_CLASSES``). This is **pilot-grade cleaning, not** the
full Engelen/Lanvin correction pipeline (which stays the confirmatory path); the
run manifest records the exact input file hashes so the pilot is reproducible.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd

# Flow-identity / timestamp columns that leak or are non-generalisable.
LEAKAGE_COLUMNS = {
    "Flow ID", "Source IP", "Src IP", "Destination IP", "Dst IP",
    "Source Port", "Src Port", "Destination Port", "Dst Port",
    "Timestamp", "Fwd Header Length.1", "SimillarHTTP", "Unnamed: 0",
}
_META = {"Label", "attack_class", "label", "target_class"}

# Multi-class target taxonomy (queue #5.1). The raw CICIDS `Label` strings are
# noisy (variant spellings, non-ASCII separators in "Web Attack \x96 ...") and
# fine-grained; this coarsens them to a stable set the detector predicts and the
# attack-class KB describes. PILOT-GRADE DEFAULT — a defensible standard CICIDS
# grouping, not yet a pre-registered config; Tier-A should promote the mapping to
# a schema-validated config and reconcile kb/attack_classes with it.
#
# Choices: DoS variants (Hulk/GoldenEye/slowloris/Slowhttptest) collapse to "DoS"
# while volumetric "DDoS" stays separate (they are distinct flow patterns); the
# three "Web Attack" variants collapse to "Web Attack"; Infiltration (~36 rows in
# full CICIDS) and Heartbleed (~11) are EXCLUDED — too few for a per-class recall
# floor — and map to None (their rows are dropped when the multi-class frame is
# built, logged there). Unknown labels also map to None (fail-safe, logged).
CANONICAL_CLASSES: tuple[str, ...] = (
    "BENIGN", "DoS", "DDoS", "PortScan", "FTP-Patator", "SSH-Patator", "Web Attack", "Bot",
)


def canonical_class(raw: str) -> str | None:
    """Map a raw CICIDS `Label` to a `CANONICAL_CLASSES` member, or None if the
    family is excluded (rare) or unknown. Whitespace-normalised, case-insensitive."""
    s = " ".join(str(raw).strip().split()).lower()
    if s == "benign":
        return "BENIGN"
    if s.startswith("web attack"):
        return "Web Attack"
    if s == "ddos":
        return "DDoS"
    if s.startswith("dos"):  # Hulk / GoldenEye / slowloris / Slowhttptest
        return "DoS"
    if s == "portscan":
        return "PortScan"
    if s == "ftp-patator":
        return "FTP-Patator"
    if s == "ssh-patator":
        return "SSH-Patator"
    if s == "bot":
        return "Bot"
    return None  # Infiltration / Heartbleed / unknown -> excluded


def class_index_map() -> dict[str, int]:
    """Canonical class name -> stable integer id (the detector's `num_class` order)."""
    return {name: i for i, name in enumerate(CANONICAL_CLASSES)}


def _strip_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    return df


def load_cicids2017(
    input_dir: str | Path, *, max_rows: int | None = None, drop_leakage: bool = True
) -> pd.DataFrame:
    """Load + minimally clean CICIDS2017 CSVs under ``input_dir``."""
    files = sorted(glob.glob(os.path.join(str(input_dir), "**", "*.csv"), recursive=True))
    if not files:
        raise FileNotFoundError(f"no CSV files found under {input_dir}")

    frames: list[pd.DataFrame] = []
    total = 0
    for f in files:
        d = _strip_columns(pd.read_csv(f, low_memory=False))
        frames.append(d)
        total += len(d)
        if max_rows is not None and total >= max_rows:
            break
    df = _strip_columns(pd.concat(frames, ignore_index=True, sort=False))

    label_col = next((c for c in df.columns if c.strip().lower() == "label"), None)
    if label_col is None:
        raise KeyError("CICIDS2017 CSVs have no 'Label' column")
    df = df.rename(columns={label_col: "Label"})
    df["attack_class"] = df["Label"].astype(str).str.strip()
    df["label"] = (df["attack_class"].str.upper() != "BENIGN").astype(int)
    # Additive multi-class target (queue #5.1); None for excluded/rare families.
    # No rows are dropped here — the binary `label` path and the toy stay unchanged;
    # `multiclass_frame` selects the valid-target rows when a K-way detector is built.
    df["target_class"] = df["attack_class"].map(canonical_class)

    if drop_leakage:
        df = df.drop(columns=[c for c in df.columns if c in LEAKAGE_COLUMNS], errors="ignore")

    feature_cols = [c for c in df.columns if c not in _META]
    df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=feature_cols).reset_index(drop=True)
    if max_rows is not None:
        df = df.iloc[:max_rows].reset_index(drop=True)
    return df


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in _META]


def multiclass_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """The K-way modelling frame (queue #5.1): rows whose ``target_class`` is a
    canonical class (excluded/rare families dropped), with an integer
    ``target_index`` column added and the ``name -> id`` map returned.

    Only classes actually present are indexed, so ``num_class`` matches the data
    (a class the sample never contains would otherwise leave XGBoost a dead slot).
    The drop count is the caller's to log."""
    valid = df[df["target_class"].notna()].reset_index(drop=True)
    present = [c for c in CANONICAL_CLASSES if c in set(valid["target_class"])]
    idx = {name: i for i, name in enumerate(present)}
    valid = valid.copy()
    valid["target_index"] = valid["target_class"].map(idx).astype(int)
    return valid, idx


def stratified_explanation_sample(
    df: pd.DataFrame,
    *,
    n_explain: int,
    seed: int,
    stratify: str = "attack_class",
    minority_floor: int = 30,
    train_frac: float = 0.7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deterministic train / explanation-set split.

    The training frame trains the detector; the explanation frame (``n_explain``
    rows, stratified by ``stratify`` with a per-class minority floor) is what gets
    explained. Same seed ⇒ same split.
    """
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(df))
    cut = int(round(len(df) * train_frac))
    train_idx, pool_idx = idx[:cut], idx[cut:]
    train_df = df.iloc[sorted(train_idx.tolist())].reset_index(drop=True)
    pool = df.iloc[sorted(pool_idx.tolist())].reset_index(drop=True)

    classes = sorted(pool[stratify].unique().tolist(), key=str)
    per_class = max(1, n_explain // max(1, len(classes)))
    picks: list[int] = []
    for cls in classes:
        cls_idx = pool.index[pool[stratify] == cls].to_numpy()
        cls_idx = cls_idx[rng.permutation(len(cls_idx))]
        take = min(len(cls_idx), max(per_class, min(minority_floor, len(cls_idx))))
        picks.extend(cls_idx[:take].tolist())
    picks = sorted(set(picks))[:n_explain] if len(picks) > n_explain else sorted(set(picks))
    explain_df = pool.iloc[picks].reset_index(drop=True)
    return train_df, explain_df
