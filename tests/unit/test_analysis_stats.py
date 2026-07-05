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


def test_variance_shares_bounded():
    sh = variance_shares([1, 2, 3, 4, 5, 6], {"g": ["a", "a", "a", "b", "b", "b"]})
    assert 0.0 <= sh["g"] <= 1.0
    assert "residual" in sh
