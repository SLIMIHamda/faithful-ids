"""Frozen split materialisation (L1).

Produces deterministic, row-level train/dev/test index files and a
``split_manifest.json`` (seed, stratification spec, class counts, source data
hash). Split indices are small and load-bearing, so they live in git; the
payloads they index are DVC-tracked. Same seed ⇒ byte-identical splits
(determinism gate).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from faithfulids.datasets.corrections.pipeline import dataframe_sha256

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

SPLIT_MANIFEST = "split_manifest.json"


@dataclass
class SplitManifest:
    dataset_id: str
    seed: int
    strategy: str
    ratios: dict[str, float]
    stratify_by: str
    n_total: int
    class_counts: dict[str, dict[str, int]]
    source_data_sha256: str
    index_files: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "dataset_id": self.dataset_id,
            "seed": self.seed,
            "strategy": self.strategy,
            "ratios": self.ratios,
            "stratify_by": self.stratify_by,
            "n_total": self.n_total,
            "class_counts": self.class_counts,
            "source_data_sha256": self.source_data_sha256,
            "index_files": self.index_files,
        }


def _stratified_indices(
    labels: np.ndarray, ratios: dict[str, float], seed: int
) -> dict[str, np.ndarray]:
    """Deterministic per-class stratified partition into train/dev/test."""
    rng = np.random.RandomState(seed)
    train_idx: list[int] = []
    dev_idx: list[int] = []
    test_idx: list[int] = []
    for cls in sorted(np.unique(labels).tolist(), key=str):
        idx = np.where(labels == cls)[0]
        idx = idx[rng.permutation(len(idx))]
        n = len(idx)
        n_train = int(round(n * ratios["train"]))
        n_dev = int(round(n * ratios["dev"]))
        train_idx.extend(idx[:n_train].tolist())
        dev_idx.extend(idx[n_train : n_train + n_dev].tolist())
        test_idx.extend(idx[n_train + n_dev :].tolist())
    return {
        "train": np.array(sorted(train_idx), dtype=int),
        "dev": np.array(sorted(dev_idx), dtype=int),
        "test": np.array(sorted(test_idx), dtype=int),
    }


def materialise_splits(
    df: "pd.DataFrame",
    *,
    dataset_id: str,
    ratios: dict[str, float],
    stratify_by: str,
    seed: int,
    out_dir: str | Path,
) -> SplitManifest:
    """Write frozen split index files + split_manifest.json into ``out_dir``."""
    if stratify_by not in df.columns:
        raise KeyError(f"stratify_by column {stratify_by!r} not in dataframe")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    labels = df[stratify_by].to_numpy()
    splits = _stratified_indices(labels, ratios, seed)

    class_counts: dict[str, dict[str, int]] = {}
    index_files: dict[str, str] = {}
    for name, idx in splits.items():
        fname = f"{name}.idx"
        (out / fname).write_text(
            "\n".join(str(i) for i in idx.tolist()) + ("\n" if len(idx) else ""),
            encoding="utf-8",
        )
        index_files[name] = fname
        sub = labels[idx]
        class_counts[name] = {
            str(c): int((sub == c).sum()) for c in sorted(np.unique(labels).tolist(), key=str)
        }

    manifest = SplitManifest(
        dataset_id=dataset_id,
        seed=seed,
        strategy="stratified_holdout",
        ratios=ratios,
        stratify_by=stratify_by,
        n_total=int(len(df)),
        class_counts=class_counts,
        source_data_sha256=dataframe_sha256(df),
        index_files=index_files,
    )
    (out / SPLIT_MANIFEST).write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
