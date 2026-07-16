"""XGBoost training entrypoint (L2, anchor detector).

Training writes a frozen booster to ``models/``; exact TreeSHAP is admissible on
the frozen booster (CPU, byte-identical). ``predict.py`` never imports this
module (edge 6). ``xgboost`` is a hard, pinned dependency imported at top level —
there is no optional-import fallback for a scientific component.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    class_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Fit an XGBoost booster, freeze it, and return training metrics.

    ``class_names`` positionally labels the label column's integer codes and is
    frozen next to the model so inference never has to guess what a probability
    column means (queue #5.2). A ``multi:*`` objective REQUIRES it (it sets
    ``num_class``); a binary objective defaults to ``[BENIGN, ATTACK]``.
    """
    objective = hyperparameters["objective"]
    multiclass = str(objective).startswith("multi:")
    if multiclass and not class_names:
        raise ValueError(f"objective {objective!r} requires class_names (sets num_class)")
    names = list(class_names) if class_names else ["BENIGN", "ATTACK"]

    feature_names = [c for c in df.columns if c != label_column]
    dtrain = xgb.DMatrix(df[feature_names].to_numpy(), label=df[label_column].to_numpy(),
                         feature_names=feature_names)
    params = {
        "objective": objective,
        "max_depth": int(hyperparameters["max_depth"]),
        "eta": float(hyperparameters["learning_rate"]),
        "subsample": float(hyperparameters["subsample"]),
        "colsample_bytree": float(hyperparameters["colsample_bytree"]),
        "min_child_weight": float(hyperparameters["min_child_weight"]),
        "tree_method": hyperparameters.get("tree_method", "hist"),
        "seed": seed,
    }
    if multiclass:
        params["num_class"] = len(names)
    booster = xgb.train(params, dtrain, num_boost_round=int(hyperparameters["n_estimators"]))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(out / MODEL_FILE))
    (out / "feature_names.json").write_text(
        json.dumps(feature_names), encoding="utf-8"
    )
    (out / "class_names.json").write_text(json.dumps(names), encoding="utf-8")

    metrics = {
        "family": "xgboost",
        "seed": seed,
        "n_train": int(len(df)),
        "n_features": len(feature_names),
        "num_boost_round": int(hyperparameters["n_estimators"]),
        "objective": objective,
        "class_names": names,
    }
    write_training_metrics(out, metrics)
    return metrics
