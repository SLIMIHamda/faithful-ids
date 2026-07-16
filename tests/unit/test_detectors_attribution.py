"""Detectors L2 (frozen-artifact boundary) and attribution cache."""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from faithfulids.attribution import AttributionCache, attribution_cache_key
from faithfulids.detectors import load_frozen
from faithfulids.detectors.random_forest.train import train
from faithfulids.framework import AttributionArtifact

SRC = Path(__file__).resolve().parents[2] / "src" / "faithfulids"


def _toy_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "f1": [0.1, 0.9, 0.2, 0.8, 0.15, 0.85, 0.25, 0.75],
            "f2": [0.0, 1.0, 0.1, 0.9, 0.05, 0.95, 0.2, 0.8],
            "Label": [0, 1, 0, 1, 0, 1, 0, 1],
        }
    )


def test_rf_train_then_frozen_predict_roundtrip(tmp_path):
    df = _toy_df()
    metrics = train(
        df,
        label_column="Label",
        hyperparameters={"n_estimators": 20, "max_depth": None, "n_jobs": 1},
        seed=42,
        out_dir=tmp_path,
    )
    assert metrics["family"] == "random_forest"

    detector = load_frozen("random_forest", tmp_path)
    assert detector.feature_names == ("f1", "f2")
    assert detector.native_model is not None  # exposed for tree attributors

    rows = [{"f1": 0.1, "f2": 0.0}, {"f1": 0.9, "f2": 1.0}]
    # per-class contract (queue #5.2): (n_samples, n_classes), columns labelled
    assert detector.class_names == ("BENIGN", "ATTACK")
    probs = detector.predict_proba(rows)
    assert len(probs) == 2 and all(len(r) == 2 for r in probs)
    assert all(0.0 <= p <= 1.0 for r in probs for p in r)
    assert all(abs(sum(r) - 1.0) < 1e-9 for r in probs)
    assert set(detector.predicted_class(rows)) <= {"BENIGN", "ATTACK"}


def test_inference_module_does_not_import_training(tmp_path):
    """Edge 6, locally: predict.py must not import the training entrypoint."""
    src = (SRC / "detectors" / "random_forest" / "predict.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert not any("train" in m for m in imported)


def test_attribution_cache_content_addressed(tmp_path):
    cache = AttributionCache(tmp_path)
    key = attribution_cache_key(model_sha256="a" * 64, data_sha256="b" * 64, config_sha256="c" * 64)
    assert cache.get(key) is None  # miss

    artifacts = [
        AttributionArtifact(
            instance_id="i0",
            feature_names=("f1", "f2"),
            values=(0.3, -0.1),
            base_value=0.5,
            method="treeshap",
            exact=True,
            background_policy="tree_path_dependent",
        )
    ]
    cache.put(key, artifacts, inputs={"model_sha256": "a" * 64})
    got = cache.get(key)
    assert got is not None and got[0] == artifacts[0]


def test_attribution_cache_key_changes_with_inputs():
    base = dict(model_sha256="a" * 64, data_sha256="b" * 64, config_sha256="c" * 64)
    k1 = attribution_cache_key(**base)
    k2 = attribution_cache_key(**dict(base, data_sha256="d" * 64))
    assert k1 != k2
    # background changes the key too (DeepSHAP)
    k3 = attribution_cache_key(**base, background_sha256="e" * 64)
    assert k3 != k1
