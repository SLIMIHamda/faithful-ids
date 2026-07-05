"""Real CICIDS2017 loader (L1).

Reads the CICIDS2017 CSVs as distributed (or an upstream-corrected variant) from
a directory — on Kaggle this is a mounted dataset. Performs the minimal,
uncontroversial cleaning a *pilot* needs (strip column names, drop flow-identity
/ timestamp leakage columns, coerce features numeric, drop NaN/Inf rows, derive
``attack_class`` + binary ``label``). This is **pilot-grade cleaning, not** the
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
_META = {"Label", "attack_class", "label"}


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
