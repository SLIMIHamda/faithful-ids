"""Layer-2 saturation diagnostic: probability space hides a signal margin reveals."""

from __future__ import annotations

import math

from faithfulids.framework import AttributionArtifact, ClaimSet, ClaimTuple, Direction
from faithfulids.metrics.layer2 import SimpleBackgroundErasure
from faithfulids.metrics.layer2.saturation import _summary, saturation_report


class _SaturatedDetector:
    """p≈0.9995 full, ≈0.994 when A is erased (A→0) — near-certain, so prob Δ≈0."""

    feature_names = ("A", "B")
    class_names = ("BENIGN", "ATTACK")

    def _p_attack(self, rows):
        return [0.9995 if r["A"] >= 1.0 else 0.994 for r in rows]

    def predict_proba(self, rows):  # per-class contract (queue #5.2)
        return [[1.0 - p, p] for p in self._p_attack(rows)]

    def predict_margin(self, rows):  # per-class (n,K) contract (queue #5.4)
        return [[-math.log(p / (1.0 - p)), math.log(p / (1.0 - p))]
                for p in self._p_attack(rows)]


def test_summary_reports_saturation_factor():
    s = _summary([0.0055, 0.0055], [2.49, 2.49])
    assert s["frac_zero_prob"] == 0.0
    assert s["mean_abs_prob"] < 0.01
    assert s["margin_over_prob"] > 100


def test_saturation_report_distinguishes_prob_from_margin():
    det = _SaturatedDetector()
    instances = {"i0": {"A": 1.0, "B": 1.0}}
    attributions = {
        "i0": AttributionArtifact("i0", ("A", "B"), (0.9, 0.1), 0.0, "x", True, "ref")
    }
    claims_map = {
        ("i0", "b0_raw_shap"): ClaimSet(
            "i0", (ClaimTuple("A", Direction.POSITIVE, rank=1),), "e", "1.0.0", "0" * 64
        )
    }
    er = SimpleBackgroundErasure({"A": 0.0, "B": 0.0})

    rep = saturation_report(det, instances, attributions, claims_map, er, k_values=[1])

    att = rep["eps_att.comprehensiveness.k1"]
    assert att["mean_abs_prob"] < 0.01      # prob space: looks like ≈0 (the v1 symptom)
    assert att["mean_abs_margin"] > 2.0     # margin space: a large log-odds move
    assert att["margin_over_prob"] > 100    # -> saturation, not a broken erasure

    mod = rep["eps_model.comprehensiveness_cited.k1"]
    assert mod["mean_abs_margin"] > 2.0     # erasing the cited feature moves it too
