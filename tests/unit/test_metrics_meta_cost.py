"""RQ0 meta-validation, plausibility validation, and cost accounting."""

from __future__ import annotations

import pytest

from faithfulids.metrics.cost import cost_accounting
from faithfulids.metrics.meta import fluency_correlation, roc_auc, sensitivity_specificity
from faithfulids.metrics.plausibility import parse_judge_scores, validate_judge


def test_perfect_metric_has_sens_spec_one():
    # faithful (label 0) score high, corrupted (label 1) score low
    scores = [0.9, 0.85, 0.8, 0.1, 0.2, 0.15]
    labels = [0, 0, 0, 1, 1, 1]
    ss = sensitivity_specificity(scores, labels, threshold=0.5, lower_is_corrupt=True)
    assert ss["sensitivity"] == 1.0 and ss["specificity"] == 1.0
    assert roc_auc(scores, labels, lower_is_corrupt=True) == pytest.approx(1.0)


def test_fluency_independent_metric_has_low_correlation():
    metric = [0.8, 0.8, 0.8, 0.8]
    fluency = [0.1, 0.9, 0.2, 0.7]
    assert abs(fluency_correlation(metric, fluency)) <= 0.5


def test_parse_and_validate_judge():
    scores = parse_judge_scores('noise {"clarity": 4, "helpfulness": 5, "believability": 3} noise')
    assert scores == {"clarity": 4.0, "helpfulness": 5.0, "believability": 3.0}
    assert parse_judge_scores("no json here") is None
    v = validate_judge([1, 2, 3, 4], [1, 2, 3, 4], threshold=0.6)
    assert v["passed"] is True and v["rho"] == pytest.approx(1.0)
    v2 = validate_judge([1, 2, 3, 4], [4, 3, 2, 1], threshold=0.6)
    assert v2["passed"] is False


def test_cost_accounting_coverage_and_tokens():
    records = [
        {"tokens": 100, "latency_ms": 10.0},
        {"tokens": 200, "latency_ms": 30.0},
    ]
    abstentions = [False, True, False, False]  # 1 of 4 abstained
    acc = cost_accounting(records, abstentions, price_per_1k_tokens=2.0)
    assert acc["total_tokens"] == 300
    assert acc["mean_latency_ms"] == pytest.approx(20.0)
    assert acc["coverage"] == pytest.approx(0.75)
    assert acc["abstention_rate"] == pytest.approx(0.25)
    assert acc["dollars"] == pytest.approx(0.6)
