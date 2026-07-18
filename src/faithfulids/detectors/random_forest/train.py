"""Random Forest training entrypoint (L2, Tier-B continuity).

Training writes a frozen artifact to ``models/``; it is the ONLY place RF fitting
happens. Deterministic given the seed (CPU). ``predict.py`` never imports this
module (import-linter edge 6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

from faithfulids.detectors.base import save_pickle_model, write_training_metrics


def train(
    df: pd.DataFrame,
    *,
    label_column: str,
    hyperparameters: Mapping[str, Any],
    seed: int,
    out_dir: str | Path,
    class_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Fit RF, freeze it to ``out_dir``, and return training metrics.

    ``class_names`` positionally labels the label column's integer codes (the
    K-way ``target_index`` path, mirroring the xgboost trainer): sklearn orders
    ``predict_proba`` columns by sorted ``classes_``, which for a 0..K-1 integer
    target is exactly the ``class_names`` order. Frozen into the artifact so
    inference never guesses column meaning.
    """
    feature_names = [c for c in df.columns if c != label_column]
    X = df[feature_names].to_numpy()
    y = df[label_column].to_numpy()

    clf = RandomForestClassifier(
        n_estimators=int(hyperparameters["n_estimators"]),
        max_depth=hyperparameters.get("max_depth"),
        min_samples_leaf=int(hyperparameters.get("min_samples_leaf", 1)),
        criterion=str(hyperparameters.get("criterion", "gini")),
        bootstrap=bool(hyperparameters.get("bootstrap", True)),
        n_jobs=int(hyperparameters.get("n_jobs", 1)),
        random_state=seed,
    )
    clf.fit(X, y)

    classes = list(clf.classes_)
    if class_names is not None and list(classes) != list(range(len(class_names))):
        raise ValueError(
            f"class_names given but the label column is not a dense 0..K-1 target: "
            f"sklearn classes_ = {classes} vs {len(class_names)} names"
        )
    positive_index = classes.index(max(classes))
    blob = {
        "estimator": clf,
        "feature_names": feature_names,
        "positive_index": positive_index,
    }
    if class_names is not None:
        blob["class_names"] = list(class_names)
    save_pickle_model(out_dir, blob)

    binary = len(classes) == 2
    proba = clf.predict_proba(X)[:, positive_index] if binary else None
    metrics = {
        "family": "random_forest",
        "seed": seed,
        "n_train": int(len(df)),
        "n_features": len(feature_names),
        "n_classes": len(classes),
        "class_names": list(class_names) if class_names is not None else None,
        "train_auc": (
            float(roc_auc_score(y, proba)) if binary and len(set(y.tolist())) > 1 else None
        ),
    }
    write_training_metrics(out_dir, metrics)
    return metrics
