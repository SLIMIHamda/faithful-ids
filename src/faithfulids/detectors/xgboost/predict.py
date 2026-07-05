"""XGBoost inference (L2). Loads a frozen booster ONLY (edge 6)."""

from __future__ import annotations

import json
from pathlib import Path

import xgboost as xgb

from faithfulids.detectors.base import MODEL_FILE, FrozenDetector


def load(model_dir: str | Path) -> FrozenDetector:
    d = Path(model_dir)
    booster = xgb.Booster()
    booster.load_model(str(d / MODEL_FILE))
    feature_names = json.loads((d / "feature_names.json").read_text(encoding="utf-8"))

    def proba(matrix):
        dm = xgb.DMatrix(matrix, feature_names=feature_names)
        return booster.predict(dm)

    return FrozenDetector(feature_names, proba, native_model=booster)
