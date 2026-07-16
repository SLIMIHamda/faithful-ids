"""Real CICIDS2017 loader (L1).

Reads the CICIDS2017 CSVs as distributed (or an upstream-corrected variant) from
a directory — on Kaggle this is a mounted dataset. Performs the minimal,
uncontroversial cleaning a *pilot* needs (strip column names, drop flow-identity
/ timestamp leakage columns, coerce features numeric, drop NaN/Inf rows, derive
``attack_class``, binary ``label``, and the coarsened multi-class ``target_class``
— see ``configs/taxonomy/``). This is **pilot-grade cleaning, not** the
full Engelen/Lanvin correction pipeline (which stays the confirmatory path); the
run manifest records the exact input file hashes so the pilot is reproducible.
"""

from __future__ import annotations

import glob
import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from faithfulids.provenance import repo_root  # L0 repo-root discovery (layer-safe)

# Flow-identity / timestamp columns that leak or are non-generalisable.
LEAKAGE_COLUMNS = {
    "Flow ID", "Source IP", "Src IP", "Destination IP", "Dst IP",
    "Source Port", "Src Port", "Destination Port", "Dst Port",
    "Timestamp", "Fwd Header Length.1", "SimillarHTTP", "Unnamed: 0",
}
_META = {"Label", "attack_class", "label", "target_class"}

# Multi-class target taxonomy (queue #5.1 / #5.1b). The canonical class set and the
# raw-label -> canonical mapping live in ONE schema-validated config,
# configs/taxonomy/<dataset>.yaml, which the attack-class KB is also validated
# against (validate-configs) so the two cannot drift silently. The loader reads
# that config directly (repo-root file read — NO orchestration/L5 import) instead
# of hard-coding the taxonomy. PILOT-GRADE DEFAULT — see the config header.


def _taxonomy_path(dataset: str) -> Path:
    return repo_root() / "configs" / "taxonomy" / f"{dataset}.yaml"


@lru_cache(maxsize=4)
def load_taxonomy(dataset: str = "cicids2017") -> dict:
    """The class taxonomy for ``dataset`` (single source of truth)."""
    with open(_taxonomy_path(dataset), "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _norm(raw: str) -> str:
    """Normalise a raw label for taxonomy lookup: lowercase, every run of
    non-alphanumeric chars -> a single space, stripped (so 'FTP-Patator',
    'Web Attack \\x96 XSS', 'DoS Hulk' become 'ftp patator', 'web attack xss',
    'dos hulk'). Must match the normalisation validate-configs uses."""
    return re.sub(r"[^a-z0-9]+", " ", str(raw).lower()).strip()


def canonical_classes(taxonomy: dict | None = None) -> tuple[str, ...]:
    """The ordered canonical target classes (the detector's num_class order)."""
    return tuple((taxonomy or load_taxonomy())["canonical_classes"])


def canonical_class(raw: str, taxonomy: dict | None = None) -> str | None:
    """Map a raw CICIDS `Label` to a canonical class, or None if the family is
    excluded (rare) or unknown — resolved through the taxonomy config."""
    tax = taxonomy or load_taxonomy()
    val = tax["label_map"].get(_norm(raw))
    return val if val in set(tax["canonical_classes"]) else None  # 'excluded'/unknown -> None


def class_index_map(taxonomy: dict | None = None) -> dict[str, int]:
    """Canonical class name -> stable integer id (the detector's `num_class` order)."""
    return {name: i for i, name in enumerate(canonical_classes(taxonomy))}


def _strip_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    return df


def load_cicids2017(
    input_dir: str | Path,
    *,
    max_rows: int | None = None,
    drop_leakage: bool = True,
    rows_per_file: int | None = None,
) -> pd.DataFrame:
    """Load + minimally clean CICIDS2017 CSVs under ``input_dir``.

    ``max_rows`` is a GLOBAL cap that appends whole files in sorted-name order and
    stops — so a small cap keeps only the first day's file(s) and therefore only
    that day's attack families (the first CICIDS file alone exceeds 200k rows).
    Fine for the binary pilot (kept byte-identical for replay); it STARVES a
    multi-class run. ``rows_per_file`` instead takes a deterministic evenly-spaced
    (stride) subsample of EACH file, so every day — and hence every canonical
    attack family — survives a memory cap. Stride, not head: attacks are
    time-blocked within a day too (e.g. FTP-Patator morning, SSH-Patator
    afternoon), so a per-file head would still drop families.
    """
    files = sorted(glob.glob(os.path.join(str(input_dir), "**", "*.csv"), recursive=True))
    if not files:
        raise FileNotFoundError(f"no CSV files found under {input_dir}")

    frames: list[pd.DataFrame] = []
    total = 0
    for f in files:
        d = _strip_columns(pd.read_csv(f, low_memory=False))
        if rows_per_file is not None and len(d) > rows_per_file:
            stride = -(-len(d) // rows_per_file)  # ceil
            d = d.iloc[::stride].iloc[:rows_per_file].reset_index(drop=True)
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
    _tax = load_taxonomy()
    df["target_class"] = df["attack_class"].map(lambda r: canonical_class(r, _tax))

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
    present = [c for c in canonical_classes() if c in set(valid["target_class"])]
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
    truncation: str = "index",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deterministic train / explanation-set split.

    The training frame trains the detector; the explanation frame (``n_explain``
    rows, stratified by ``stratify`` with a per-class minority floor) is what gets
    explained. Same seed ⇒ same split. Rows whose ``stratify`` value is NA (e.g.
    excluded-family ``target_class``) are never explained and do not count as a
    stratum.

    ``truncation`` decides which picks survive when the per-class quotas overshoot
    ``n_explain``. ``"index"`` (legacy) keeps the lowest pool indices — BIASED for
    CICIDS, whose classes are contiguous per-day file blocks (late-day classes can
    vanish from the explained set entirely), but frozen: it is what every cached
    binary run used, so changing it would break token-free replay. ``"round_robin"``
    drops picks evenly across classes (one per class per round), guaranteeing every
    stratum keeps ~n/K rows — required for the K-way detector, whose competence
    gate measures per-class recall ON this set.
    """
    if truncation not in ("index", "round_robin"):
        raise ValueError(f"unknown truncation {truncation!r} (expected 'index' or 'round_robin')")
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(df))
    cut = int(round(len(df) * train_frac))
    train_idx, pool_idx = idx[:cut], idx[cut:]
    train_df = df.iloc[sorted(train_idx.tolist())].reset_index(drop=True)
    pool = df.iloc[sorted(pool_idx.tolist())].reset_index(drop=True)

    classes = sorted(pool[stratify].dropna().unique().tolist(), key=str)
    per_class = max(1, n_explain // max(1, len(classes)))
    picks_by_class: list[list[int]] = []
    for cls in classes:
        cls_idx = pool.index[pool[stratify] == cls].to_numpy()
        cls_idx = cls_idx[rng.permutation(len(cls_idx))]
        take = min(len(cls_idx), max(per_class, min(minority_floor, len(cls_idx))))
        picks_by_class.append(cls_idx[:take].tolist())
    picks = [i for cls_picks in picks_by_class for i in cls_picks]
    if len(picks) > n_explain:
        if truncation == "round_robin":
            kept: list[int] = []
            for round_i in range(max(len(p) for p in picks_by_class)):
                for cls_picks in picks_by_class:
                    if round_i < len(cls_picks):
                        kept.append(cls_picks[round_i])
                        if len(kept) == n_explain:
                            break
                if len(kept) == n_explain:
                    break
            picks = sorted(set(kept))
        else:
            picks = sorted(set(picks))[:n_explain]
    else:
        picks = sorted(set(picks))
    explain_df = pool.iloc[picks].reset_index(drop=True)
    return train_df, explain_df
