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
import warnings
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


#: The benign class name. ``predict_attack_proba`` is defined as ``1 - P(BENIGN)``,
#: so every taxonomy must name its negative class exactly this.
BENIGN_CLASS = "BENIGN"


def _as_rows(out: Any, n: int) -> list[list[float]]:
    """Normalise a family's proba/margin output to ``(n, n_classes)``.

    A binary head may report a single attack probability per row (shape ``(n,)``);
    it becomes ``[P(BENIGN), P(ATTACK)] = [1-p, p]`` so every family satisfies the
    same per-class contract (queue #5.2).
    """
    rows = [r for r in out]
    if rows and not hasattr(rows[0], "__len__"):
        return [[1.0 - float(p), float(p)] for p in rows]
    return [[float(x) for x in r] for r in rows]


class FrozenDetector:
    """A frozen detector loaded for inference (framework.DetectorArtifact)."""

    def __init__(
        self,
        feature_names: Sequence[str],
        proba: Callable[[Sequence[Sequence[float]]], Sequence[Any]],
        class_names: Sequence[str] = ("BENIGN", "ATTACK"),
        native_model: Any | None = None,
        margin: Callable[[Sequence[Sequence[float]]], Sequence[Any]] | None = None,
    ) -> None:
        self._feature_names = tuple(feature_names)
        self._proba = proba
        #: positional labels for predict_proba's columns (queue #5.2) — the
        #: detector's own record of what its outputs MEAN, so no consumer has to
        #: assume a column order.
        self._class_names = tuple(class_names)
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

    @property
    def class_names(self) -> tuple[str, ...]:
        return self._class_names

    @property
    def n_classes(self) -> int:
        return len(self._class_names)

    def _matrix(self, rows: Sequence[Mapping[str, float]]) -> list[list[float]]:
        return [[float(r[f]) for f in self._feature_names] for r in rows]

    def predict_proba(self, rows: Sequence[Mapping[str, float]]) -> list[list[float]]:
        """Per-class probabilities, shape ``(n_samples, n_classes)`` — columns are
        positionally labelled by ``class_names`` (queue #5.2)."""
        out = _as_rows(self._proba(self._matrix(rows)), len(rows))
        for r in out:
            if len(r) != self.n_classes:
                raise ValueError(
                    f"detector returned {len(r)} probabilities but class_names has "
                    f"{self.n_classes} entries: {self._class_names}"
                )
        return out

    def predicted_class(self, rows: Sequence[Mapping[str, float]]) -> list[str]:
        """The argmax class NAME per row."""
        return [self._class_names[max(range(len(r)), key=r.__getitem__)]
                for r in self.predict_proba(rows)]

    def predict_attack_proba(self, rows: Sequence[Mapping[str, float]]) -> list[float]:
        """DEPRECATED legacy shim: one scalar "attack probability" per row, defined
        **exactly** as ``1 - P(BENIGN)``.

        Kept so pre-multi-class callers (and older notebooks/experiments) keep
        running while they migrate to the per-class ``predict_proba``. Removed
        after the pilot — new code should read ``predict_proba`` +
        ``class_names`` / ``predicted_class`` instead.
        """
        warnings.warn(
            "predict_attack_proba() is a deprecated binary shim (1 - P(BENIGN)); "
            "use predict_proba() with class_names / predicted_class. "
            "It is removed after the pilot.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._attack_proba(rows)

    def _attack_proba(self, rows: Sequence[Mapping[str, float]]) -> list[float]:
        """``1 - P(BENIGN)`` without the deprecation warning (internal migration use)."""
        if BENIGN_CLASS not in self._class_names:
            raise ValueError(
                f"attack probability is defined as 1 - P({BENIGN_CLASS}), but this "
                f"detector's classes are {self._class_names}"
            )
        b = self._class_names.index(BENIGN_CLASS)
        return [1.0 - r[b] for r in self.predict_proba(rows)]

    def predict_margin(self, rows: Sequence[Mapping[str, float]]) -> list[list[float]]:
        """Per-class margin (raw log-odds), shape ``(n_samples, n_classes)`` —
        mirroring ``predict_proba`` (queue #5.4). Consumed by margin-space Layer-2
        deltas, which avoid probability saturation when the model is near-certain;
        Layer-2 reads the column of the class the attribution explains.

        Uses the native margin when the family provides one; otherwise falls back
        to ``logit(clip(1 - P(BENIGN)))`` — exact for a binary-logistic head where
        ``p = sigmoid(margin)``, monotone otherwise. A binary head reports a single
        attack-side margin ``m``; the benign column is exactly ``-m``, since
        ``logit(P(BENIGN)) = logit(1 - sigmoid(m)) = -m``.
        """
        if self._margin is not None:
            raw = [m for m in self._margin(self._matrix(rows))]
            if raw and hasattr(raw[0], "__len__"):
                return [[float(x) for x in r] for r in raw]
            return [[-float(m), float(m)] for m in raw]  # binary head -> [BENIGN, ATTACK]
        if self.n_classes != 2:
            raise NotImplementedError(
                "a multi-class head must expose a native per-class margin; the logit "
                "fallback is only defined for a binary head."
            )
        eps = 1e-6
        out: list[list[float]] = []
        for p in self._attack_proba(rows):
            p = min(1.0 - eps, max(eps, float(p)))
            m = math.log(p / (1.0 - p))
            out.append([-m, m])
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
