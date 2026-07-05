"""Datasets L1: correction pipeline (hard-fail), split materialisation, integrity."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from faithfulids.datasets.corrections import (
    ChecksumMismatch,
    UnimplementedCorrection,
    build_pipeline,
    dataframe_sha256,
)
from faithfulids.datasets.corrections.engelen_lanvin import PIPELINE_VERSION
from faithfulids.datasets.integrity_check import check
from faithfulids.datasets.splits import materialise_splits


def _toy_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "f1": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            "f2": [1, 0, 1, 0, 1, 0, 1, 0],
            "Label": [0, 0, 0, 0, 1, 1, 1, 1],
        }
    )


def test_correction_pipeline_hard_fails_never_passes_through():
    df = _toy_df()
    pipeline = build_pipeline()
    with pytest.raises(UnimplementedCorrection):
        pipeline.apply(df)


def test_correction_pipeline_describe_and_version():
    pipeline = build_pipeline()
    assert pipeline.version == PIPELINE_VERSION
    names = [r["name"] for r in pipeline.describe()]
    assert "drop_duplicate_flows" in names
    assert len(names) == len(set(names))


def test_correction_checksum_mismatch_is_refused():
    df = _toy_df()
    pipeline = build_pipeline()
    with pytest.raises(ChecksumMismatch):
        pipeline.apply(df, expected_input_sha256="0" * 64)


def test_materialise_splits_is_deterministic_and_manifested(tmp_path):
    df = _toy_df()
    ratios = {"train": 0.5, "dev": 0.25, "test": 0.25}
    a = tmp_path / "a"
    b = tmp_path / "b"
    m1 = materialise_splits(df, dataset_id="toy", ratios=ratios, stratify_by="Label", seed=7, out_dir=a)
    m2 = materialise_splits(df, dataset_id="toy", ratios=ratios, stratify_by="Label", seed=7, out_dir=b)

    # byte-identical split index files for the same seed (determinism)
    for name in ("train", "dev", "test"):
        assert (a / f"{name}.idx").read_bytes() == (b / f"{name}.idx").read_bytes()

    manifest = json.loads((a / "split_manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 7
    assert manifest["source_data_sha256"] == dataframe_sha256(df)
    total = sum(sum(c.values()) for c in manifest["class_counts"].values())
    assert total == len(df)


def test_materialise_splits_rejects_missing_stratify_column(tmp_path):
    with pytest.raises(KeyError):
        materialise_splits(
            _toy_df(), dataset_id="toy", ratios={"train": 0.6, "dev": 0.2, "test": 0.2},
            stratify_by="nope", seed=1, out_dir=tmp_path,
        )


def test_integrity_check_passes_on_pending_checksums():
    assert check() == []
