"""Layer-2 metrics vs the hand-computed fixture + the imputation erasure operator."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from faithfulids.framework import AttributionArtifact
from faithfulids.metrics.layer2 import (
    ConditionalExpectationImputer,
    SimpleBackgroundErasure,
    comprehensiveness,
    sufficiency,
)

FIXTURE = Path(__file__).resolve().parents[1] / "metrics_fixtures" / "layer2_linear.json"


class ToyLinearDetector:
    """proba = bias + sum_f w_f * x_f (framework.DetectorArtifact)."""

    def __init__(self, bias, weights, feature_names):
        self._bias = bias
        self._w = weights
        self._fn = tuple(feature_names)

    @property
    def feature_names(self):
        return self._fn

    def predict_proba(self, rows):
        return [self._bias + sum(self._w[f] * r[f] for f in self._fn) for r in rows]


def test_layer2_matches_hand_computed_fixture():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    det = ToyLinearDetector(**fx["detector"])
    attribution = AttributionArtifact.from_dict(fx["attribution"])
    erasure = SimpleBackgroundErasure(fx["background"])
    k = fx["k"]
    assert det.predict_proba([fx["instance"]])[0] == pytest.approx(fx["expected"]["p_full"])
    assert comprehensiveness(attribution, det, fx["instance"], erasure, k=k) == pytest.approx(
        fx["expected"]["comprehensiveness"]
    )
    assert sufficiency(attribution, det, fx["instance"], erasure, k=k) == pytest.approx(
        fx["expected"]["sufficiency"]
    )


def test_conditional_expectation_imputer_is_deterministic():
    X = np.array([[0.0, 0.0], [1.0, 1.0], [0.9, 1.1], [0.1, -0.1]])
    imp = ConditionalExpectationImputer(k=2).fit(X, ["A", "B"])
    # B is an outlier (5.0); its 2 nearest neighbours by A (0.95) are rows with
    # B = 1.0 and 1.1, so the imputed B is their mean 1.05 — not the input 5.0.
    a = imp.erase({"A": 0.95, "B": 5.0}, ["B"])
    b = imp.erase({"A": 0.95, "B": 5.0}, ["B"])
    assert a == b  # deterministic
    assert a["A"] == 0.95  # retained feature untouched
    assert a["B"] == pytest.approx(1.05)  # imputed from neighbours, not kept
