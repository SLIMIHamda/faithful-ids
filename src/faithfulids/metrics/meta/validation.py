"""RQ0 meta-validation of the metrics themselves (L4).

Given a metric's values on faithful vs corrupted explanations (with the
corruption ground-truth labels), compute the metric's sensitivity / specificity
/ ROC-AUC as a corruption *detector*, and its correlation with a fluency proxy
(metrics must be weakly correlated with fluency). This is the machinery behind
gate EXP-G-002; a metric is admissible only after clearing the corruption
battery.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score


def sensitivity_specificity(
    scores: Sequence[float],
    labels: Sequence[int],
    threshold: float,
    *,
    lower_is_corrupt: bool = True,
) -> dict[str, float]:
    """labels: 1 = corrupted, 0 = faithful. A faithfulness metric that *works*
    scores corrupted explanations LOWER, so ``lower_is_corrupt`` predicts
    corruption when ``score < threshold``."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    pred = (s < threshold) if lower_is_corrupt else (s > threshold)
    tp = int(np.sum((pred == 1) & (y == 1)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    tn = int(np.sum((pred == 0) & (y == 0)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    return {"sensitivity": sens, "specificity": spec, "tp": tp, "fn": fn, "tn": tn, "fp": fp}


def roc_auc(scores: Sequence[float], labels: Sequence[int], *, lower_is_corrupt: bool = True) -> float:
    s = np.asarray(scores, dtype=float)
    signed = -s if lower_is_corrupt else s
    return float(roc_auc_score(np.asarray(labels, dtype=int), signed))


def fluency_correlation(metric_values: Sequence[float], fluency_values: Sequence[float]) -> float:
    """Spearman correlation of a metric with a fluency proxy (should be weak)."""
    if len(metric_values) < 2:
        return 0.0
    # A constant metric has undefined rank correlation -> report 0 (independent).
    if len(set(metric_values)) == 1 or len(set(fluency_values)) == 1:
        return 0.0
    rho, _p = spearmanr(metric_values, fluency_values)
    return float(rho) if rho == rho else 0.0  # NaN guard
