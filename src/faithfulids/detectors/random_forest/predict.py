"""Random Forest inference (L2). Loads a frozen artifact ONLY.

This module must never import the training entrypoint (import-linter edge 6:
inference cannot trigger training).
"""

from __future__ import annotations

from pathlib import Path

from faithfulids.detectors.base import FrozenDetector, load_pickle_model


def load(model_dir: str | Path) -> FrozenDetector:
    blob = load_pickle_model(model_dir)
    estimator = blob["estimator"]
    feature_names = blob["feature_names"]
    positive_index = blob["positive_index"]

    def proba(matrix):
        return estimator.predict_proba(matrix)[:, positive_index]

    return FrozenDetector(feature_names, proba, native_model=estimator)
