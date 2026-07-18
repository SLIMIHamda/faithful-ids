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

    # Per-class contract (queue #5.2): expose sklearn's full (n, K) proba rather
    # than slicing the positive column, and label the columns.
    class_names = blob.get("class_names")
    if not class_names:
        n_classes = len(getattr(estimator, "classes_", [0, 1]))
        if n_classes != 2:
            raise ValueError(
                f"frozen random_forest has {n_classes} classes but no class_names in its "
                "artifact; retrain so the column labels are frozen with the model"
            )
        class_names = ["ATTACK", "BENIGN"] if positive_index == 0 else ["BENIGN", "ATTACK"]

    def proba(matrix):
        return estimator.predict_proba(matrix)  # (n, K), column order = estimator.classes_

    # K-way margin: log(clip(P_k)) — a monotone per-class LOG-PROBABILITY margin
    # (documented: not log-odds; RF has no native raw score). Keeps margin-space
    # Layer-2 defined on this family. The binary head keeps margin=None so the
    # established logit fallback (and every existing binary number) is unchanged.
    margin = None
    if len(class_names) > 2:
        import numpy as np

        def margin(matrix):  # noqa: F811 — conditional definition is the point
            return np.log(np.clip(estimator.predict_proba(matrix), 1e-12, 1.0))

    return FrozenDetector(
        feature_names, proba, class_names=class_names, native_model=estimator, margin=margin
    )
