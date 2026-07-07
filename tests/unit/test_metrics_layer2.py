"""Layer-2 metrics vs the hand-computed fixture + the imputation erasure operator."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from faithfulids.framework import AttributionArtifact, ClaimSet, ClaimTuple, Direction
from faithfulids.metrics.layer2 import (
    ConditionalExpectationImputer,
    SimpleBackgroundErasure,
    comprehensiveness,
    comprehensiveness_cited,
    sufficiency,
    sufficiency_cited,
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


# --------------------------------------------------------------------------- #
# ε_model (claim-driven): erase the CITED features S, hand-computed.
# Detector proba = 0.3 + 0.2·A + 0.1·B + 0.05·C; instance all-ones -> p_full=0.65.
# --------------------------------------------------------------------------- #
_DET = dict(bias=0.3, weights={"A": 0.2, "B": 0.1, "C": 0.05}, feature_names=["A", "B", "C"])
_INSTANCE = {"A": 1.0, "B": 1.0, "C": 1.0}
_BG = SimpleBackgroundErasure({"A": 0.0, "B": 0.0, "C": 0.0})


def _claimset(*claims):
    return ClaimSet(
        instance_id="i0", claims=tuple(claims),
        extractor_id="test", extractor_version="1.0.0", prompt_sha256="0" * 64,
    )


def test_eps_model_cited_erasure_hand_computed():
    det = ToyLinearDetector(**_DET)
    # Cited order by rank: B (rank 1), A (rank 2).
    claims = _claimset(
        ClaimTuple("B", Direction.POSITIVE, rank=1),
        ClaimTuple("A", Direction.POSITIVE, rank=2),
    )
    # k=1 -> S={B}: erase B -> 0.3+0.2+0.05=0.55 ; comp = 0.65-0.55 = 0.10
    assert comprehensiveness_cited(claims, det, _INSTANCE, _BG, k=1) == pytest.approx(0.10)
    # k=1 -> keep only B, erase A,C -> 0.3+0.1=0.40 ; suff = 0.65-0.40 = 0.25
    assert sufficiency_cited(claims, det, _INSTANCE, _BG, k=1) == pytest.approx(0.25)
    # k=2 -> S={B,A}: erase both -> 0.3+0.05=0.35 ; comp = 0.30
    assert comprehensiveness_cited(claims, det, _INSTANCE, _BG, k=2) == pytest.approx(0.30)


def test_eps_model_ignores_hallucinated_cited_feature():
    det = ToyLinearDetector(**_DET)
    # A rank-1 claim for a feature the detector doesn't have must be skipped, so
    # k=1 erases the next real cited feature (A), not the hallucination.
    claims = _claimset(
        ClaimTuple("NOT_A_FEATURE", Direction.POSITIVE, rank=1),
        ClaimTuple("A", Direction.POSITIVE, rank=2),
    )
    # S={A}: erase A -> 0.3+0.1+0.05=0.45 ; comp = 0.65-0.45 = 0.20
    assert comprehensiveness_cited(claims, det, _INSTANCE, _BG, k=1) == pytest.approx(0.20)


def test_eps_model_cites_nothing_real_scores_zero_comprehensiveness():
    det = ToyLinearDetector(**_DET)
    claims = _claimset(ClaimTuple("ZZZ", Direction.POSITIVE, rank=1))
    # S=∅ -> erase nothing -> comp = 0 (removes nothing decision-relevant).
    assert comprehensiveness_cited(claims, det, _INSTANCE, _BG, k=3) == pytest.approx(0.0)


def test_erasure_efficacy_smoke():
    """Erase-all must move the score materially; erase-none must move it by 0.

    This CI invariant catches a no-op erasure wiring (the failure mode that made
    v1's comprehensiveness ≈ 0 everywhere) before any LLM tokens are spent.
    """
    det = ToyLinearDetector(**_DET)
    p_full = det.predict_proba([_INSTANCE])[0]
    p_none = det.predict_proba([_BG.erase(_INSTANCE, [])])[0]
    p_all = det.predict_proba([_BG.erase(_INSTANCE, ["A", "B", "C"])])[0]
    assert p_none == pytest.approx(p_full)       # erase nothing -> exactly no change
    assert abs(p_full - p_all) >= 0.3            # erase all -> large, material move


class _SaturatedDetector:
    """Near-certain detector: p≈0.9995 full, ≈0.994 when A is erased (A→0)."""

    feature_names = ("A", "B")

    def predict_proba(self, rows):
        return [0.9995 if r["A"] >= 1.0 else 0.994 for r in rows]

    def predict_margin(self, rows):
        import math

        return [math.log(p / (1.0 - p)) for p in self.predict_proba(rows)]


def test_margin_space_rescues_saturated_signal():
    det = _SaturatedDetector()
    attr = AttributionArtifact(
        instance_id="i", feature_names=("A", "B"), values=(0.9, 0.1),
        base_value=0.0, method="x", exact=True, background_policy="ref",
    )
    inst = {"A": 1.0, "B": 1.0}
    er = SimpleBackgroundErasure({"A": 0.0, "B": 0.0})
    d_prob = comprehensiveness(attr, det, inst, er, k=1, delta_space="prob")
    d_margin = comprehensiveness(attr, det, inst, er, k=1, delta_space="margin")
    assert d_prob == pytest.approx(0.0055, abs=1e-6)   # saturated: looks like ~0
    assert d_margin > 2.0                              # log-odds move is large
    assert d_margin > 100 * d_prob                     # margin space reveals it


def test_margin_space_requires_predict_margin():
    det = ToyLinearDetector(**_DET)  # no predict_margin
    attr = AttributionArtifact(
        instance_id="i", feature_names=("A", "B", "C"), values=(0.2, 0.1, 0.05),
        base_value=0.3, method="x", exact=True, background_policy="ref",
    )
    with pytest.raises(ValueError, match="predict_margin"):
        comprehensiveness(attr, det, _INSTANCE, _BG, k=1, delta_space="margin")
