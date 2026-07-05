"""Random Forest training entrypoint (L2, Tier-B continuity).

Training writes a frozen artifact to ``models/``; it is the ONLY place RF fitting
happens. Deterministic given the seed (CPU). ``predict.py`` never imports this
module (import-linter edge 6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

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
) -> dict[str, Any]:
    """Fit RF, freeze it to ``out_dir``, and return training metrics."""
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
    positive_index = classes.index(max(classes))
    blob = {
        "estimator": clf,
        "feature_names": feature_names,
        "positive_index": positive_index,
    }
    save_pickle_model(out_dir, blob)

    proba = clf.predict_proba(X)[:, positive_index]
    metrics = {
        "family": "random_forest",
        "seed": seed,
        "n_train": int(len(df)),
        "n_features": len(feature_names),
        "train_auc": float(roc_auc_score(y, proba)) if len(set(y.tolist())) > 1 else None,
    }
    write_training_metrics(out_dir, metrics)
    return metrics
