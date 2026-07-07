"""Detector training/inference artifact boundary (L2).

The requirement "detectors without mixing training and evaluation logic" is
realised as an *artifact boundary*: training writes a frozen model + manifest to
``models/``; evaluation loads frozen artifacts ONLY and can never retrain
implicitly (import-linter edge 6: ``*.predict`` may not import ``*.train``).

Detector implementations are dispatched **lazily by family** so importing this
package never drags in ``xgboost`` / ``torch`` — only the module for the family
actually used is imported (this is dispatch, not an optional-dependency
fallback).
"""

from __future__ import annotations

import importlib
import json
import math
import pickle
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

MODEL_FILE = "model.bin"
TRAINING_METRICS_FILE = "training_metrics.json"

# family -> (train module, predict module). The runner imports exactly one.
DETECTOR_MODULES: dict[str, tuple[str, str]] = {
    "xgboost": ("faithfulids.detectors.xgboost.train", "faithfulids.detectors.xgboost.predict"),
    "ft_transformer": (
        "faithfulids.detectors.ft_transformer.train",
        "faithfulids.detectors.ft_transformer.predict",
    ),
    "random_forest": (
        "faithfulids.detectors.random_forest.train",
        "faithfulids.detectors.random_forest.predict",
    ),
}


class FrozenDetector:
    """A frozen detector loaded for inference (framework.DetectorArtifact)."""

    def __init__(
        self,
        feature_names: Sequence[str],
        proba: Callable[[Sequence[Sequence[float]]], Sequence[float]],
        native_model: Any | None = None,
        margin: Callable[[Sequence[Sequence[float]]], Sequence[float]] | None = None,
    ) -> None:
        self._feature_names = tuple(feature_names)
        self._proba = proba
        #: raw log-odds / margin callable, if the family exposes one natively
        #: (e.g. XGBoost ``output_margin=True``). ``None`` -> logit fallback.
        self._margin = margin
        #: the underlying estimator (booster / sklearn model), exposed for
        #: model-specific attributors (e.g. exact TreeSHAP). ``None`` for models
        #: whose attributor does not need direct access.
        self.native_model = native_model

    @property
    def feature_names(self) -> tuple[str, ...]:
        return self._feature_names

    def _matrix(self, rows: Sequence[Mapping[str, float]]) -> list[list[float]]:
        return [[float(r[f]) for f in self._feature_names] for r in rows]

    def predict_proba(self, rows: Sequence[Mapping[str, float]]) -> list[float]:
        return [float(p) for p in self._proba(self._matrix(rows))]

    def predict_margin(self, rows: Sequence[Mapping[str, float]]) -> list[float]:
        """Attack-class margin (raw log-odds). Consumed by margin-space Layer-2
        deltas, which avoid probability saturation when the model is near-certain.

        Uses the native margin when the family provides one; otherwise falls back
        to ``logit(clip(p))`` — exact for a binary-logistic head where
        ``p = sigmoid(margin)``, monotone otherwise.
        """
        if self._margin is not None:
            return [float(m) for m in self._margin(self._matrix(rows))]
        eps = 1e-6
        out: list[float] = []
        for p in self.predict_proba(rows):
            p = min(1.0 - eps, max(eps, float(p)))
            out.append(math.log(p / (1.0 - p)))
        return out


def get_trainer(family: str):
    """Lazily import and return the training entrypoint for ``family``."""
    if family not in DETECTOR_MODULES:
        raise KeyError(f"unknown detector family: {family!r}")
    mod = importlib.import_module(DETECTOR_MODULES[family][0])
    return mod.train


def load_frozen(family: str, model_dir: str | Path) -> FrozenDetector:
    """Lazily import the predict module for ``family`` and load the frozen model."""
    if family not in DETECTOR_MODULES:
        raise KeyError(f"unknown detector family: {family!r}")
    mod = importlib.import_module(DETECTOR_MODULES[family][1])
    return mod.load(model_dir)


# --------------------------------------------------------------------------- #
# Shared serialisation helpers (used by the pickle-serialisable families).
# --------------------------------------------------------------------------- #
def save_pickle_model(model_dir: str | Path, estimator: Any) -> Path:
    d = Path(model_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / MODEL_FILE
    with open(path, "wb") as fh:
        pickle.dump(estimator, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def load_pickle_model(model_dir: str | Path) -> Any:
    with open(Path(model_dir) / MODEL_FILE, "rb") as fh:
        return pickle.load(fh)


def write_training_metrics(model_dir: str | Path, metrics: dict[str, Any]) -> Path:
    d = Path(model_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / TRAINING_METRICS_FILE
    path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
