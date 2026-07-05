"""XGBoost training entrypoint (L2, anchor detector).

Training writes a frozen booster to ``models/``; exact TreeSHAP is admissible on
the frozen booster (CPU, byte-identical). ``predict.py`` never imports this
module (edge 6). ``xgboost`` is a hard, pinned dependency imported at top level —
there is no optional-import fallback for a scientific component.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import xgboost as xgb

from faithfulids.detectors.base import MODEL_FILE, write_training_metrics


def train(
    df: pd.DataFrame,
    *,
    label_column: str,
    hyperparameters: Mapping[str, Any],
    seed: int,
    out_dir: str | Path,
) -> dict[str, Any]:
    """Fit an XGBoost booster, freeze it, and return training metrics."""
    feature_names = [c for c in df.columns if c != label_column]
    dtrain = xgb.DMatrix(df[feature_names].to_numpy(), label=df[label_column].to_numpy(),
                         feature_names=feature_names)
    params = {
        "objective": hyperparameters["objective"],
        "max_depth": int(hyperparameters["max_depth"]),
        "eta": float(hyperparameters["learning_rate"]),
        "subsample": float(hyperparameters["subsample"]),
        "colsample_bytree": float(hyperparameters["colsample_bytree"]),
        "min_child_weight": float(hyperparameters["min_child_weight"]),
        "tree_method": hyperparameters.get("tree_method", "hist"),
        "seed": seed,
    }
    booster = xgb.train(params, dtrain, num_boost_round=int(hyperparameters["n_estimators"]))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(out / MODEL_FILE))
    (out / "feature_names.json").write_text(
        json.dumps(feature_names), encoding="utf-8"
    )

    metrics = {
        "family": "xgboost",
        "seed": seed,
        "n_train": int(len(df)),
        "n_features": len(feature_names),
        "num_boost_round": int(hyperparameters["n_estimators"]),
    }
    write_training_metrics(out, metrics)
    return metrics
