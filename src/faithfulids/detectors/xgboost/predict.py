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
    # frozen alongside the model by train() (queue #5.2); older model dirs without
    # it are binary boosters -> the default [BENIGN, ATTACK].
    cn_path = d / "class_names.json"
    class_names = (
        json.loads(cn_path.read_text(encoding="utf-8")) if cn_path.is_file()
        else ["BENIGN", "ATTACK"]
    )

    def proba(matrix):
        dm = xgb.DMatrix(matrix, feature_names=feature_names)
        return booster.predict(dm)  # (n,) binary:logistic | (n,K) multi:softprob

    def margin(matrix):
        dm = xgb.DMatrix(matrix, feature_names=feature_names)
        return booster.predict(dm, output_margin=True)

    return FrozenDetector(
        feature_names, proba, class_names=class_names, native_model=booster, margin=margin
    )
