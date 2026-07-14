"""Statistical pipelines (analysis boundary A) — pure consumers, tested in isolation."""

from __future__ import annotations

import numpy as np
import pytest

from analysis.src.bootstrap_ci import bootstrap_mean_ci, cohens_d
from analysis.src.coverage_risk import risk_coverage_curve
from analysis.src.friedman_nemenyi import average_ranks, friedman_nemenyi
from analysis.src.variance_components import variance_shares
from analysis.src.wilcoxon_pairs import holm_bonferroni, wilcoxon_pair


def test_friedman_nemenyi_ranks_best_method_first():
    scores = [
        [0.90, 0.80, 0.85, 0.88, 0.86],  # method 0 always best
        [0.10, 0.20, 0.15, 0.05, 0.12],
        [0.30, 0.25, 0.20, 0.35, 0.28],
    ]
    res = friedman_nemenyi(scores, higher_is_better=True)
    assert res["n_methods"] == 3 and res["n_blocks"] == 5
    assert res["avg_ranks"][0] == min(res["avg_ranks"])
    assert res["pvalue"] < 0.05
    assert res["critical_difference"] > 0


def test_average_ranks_simple():
    r = average_ranks(np.array([[1.0, 1.0], [0.0, 0.0]]), higher_is_better=True)
    assert r[0] == 1.0 and r[1] == 2.0


def test_wilcoxon_and_holm_monotone():
    w = wilcoxon_pair([0.9, 0.8, 0.85, 0.7, 0.75], [0.1, 0.2, 0.15, 0.3, 0.25])
    assert 0.0 <= w["pvalue"] <= 1.0
    adj = holm_bonferroni({"h1": 0.01, "h2": 0.04, "h3": 0.5})
    assert adj["h1"] <= adj["h2"] <= adj["h3"]
    assert adj["h1"] == pytest.approx(0.03)


def test_bootstrap_ci_brackets_mean_and_is_reproducible():
    vals = [0.5, 0.6, 0.55, 0.52, 0.58]
    ci = bootstrap_mean_ci(vals, n_resamples=2000, seed=0)
    assert ci["ci_low"] <= ci["mean"] <= ci["ci_high"]
    assert ci == bootstrap_mean_ci(vals, n_resamples=2000, seed=0)  # seeded


def test_cohens_d_sign():
    # differences vary (non-zero variance) and are positive on average
    assert cohens_d([1.0, 2.0, 3.0, 4.0], [0.0, 1.5, 2.0, 3.0]) > 0


def test_coverage_risk_curve_is_monotone_in_coverage():
    res = risk_coverage_curve([0.0, 1.0, 0.0, 1.0], [0.9, 0.1, 0.8, 0.2])
    assert res["coverage"] == sorted(res["coverage"])
    assert res["aurc"] >= 0.0


def _row(inst, metric, value, gen="b4_vte"):
    return {"instance_id": inst, "layer": "layer1", "metric": metric,
            "value": value, "grouping": {"generator_id": gen}}


def test_gated_instance_values_excludes_undefined_but_keeps_failures():
    """NaN-exclusion aggregation: dsa_asserted gated on direction_assertion_rate
    drops no-assertion instances (structural 0.0) but KEEPS a genuinely-wrong
    asserted instance (rate>0, value 0.0) — real failures must not be hidden."""
    from analysis.run import _instance_values

    rows = [
        _row("i0", "dsa_asserted", 1.0), _row("i0", "direction_assertion_rate", 1.0),  # asserted, correct
        _row("i1", "dsa_asserted", 0.0), _row("i1", "direction_assertion_rate", 1.0),  # asserted, WRONG -> keep
        _row("i2", "dsa_asserted", 0.0), _row("i2", "direction_assertion_rate", 0.0),  # silent -> drop
    ]
    gated = _instance_values(rows, "dsa_asserted", "b4_vte", gate_metric="direction_assertion_rate")
    ungated = _instance_values(rows, "dsa_asserted", "b4_vte")
    assert gated == [1.0, 0.0]  # i2 dropped, i1 (real failure) kept
    assert sum(gated) / len(gated) == pytest.approx(0.5)
    assert ungated == [1.0, 0.0, 0.0]  # naive mean would be 0.333 — the structural-zero trap


def test_gated_instance_values_arc_pairs_threshold():
    """ARC gated on arc_n_pairs>=2 (Spearman needs >=2 points): drops <2-pair
    instances (structural 0.0) but keeps a genuine anti-correlation (pairs>=2)."""
    from analysis.run import _instance_values

    rows = [
        _row("i0", "arc", 1.0), _row("i0", "arc_n_pairs", 3.0),    # defined, kept
        _row("i1", "arc", -1.0), _row("i1", "arc_n_pairs", 2.0),   # anti-corr FAILURE -> keep
        _row("i2", "arc", 0.0), _row("i2", "arc_n_pairs", 1.0),    # < 2 pairs -> undefined -> drop
    ]
    gated = _instance_values(rows, "arc", "b4_vte", gate_metric="arc_n_pairs", gate_min=2)
    assert gated == [1.0, -1.0]  # i2 dropped; the real failure i1 stays in


def test_variance_shares_bounded():
    sh = variance_shares([1, 2, 3, 4, 5, 6], {"g": ["a", "a", "a", "b", "b", "b"]})
    assert 0.0 <= sh["g"] <= 1.0
    assert "residual" in sh
