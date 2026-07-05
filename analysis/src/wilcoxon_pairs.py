"""Wilcoxon signed-rank pairwise tests with Holm-Bonferroni within a family."""

from __future__ import annotations

from typing import Sequence

from scipy.stats import wilcoxon


def wilcoxon_pair(a: Sequence[float], b: Sequence[float]) -> dict:
    stat, p = wilcoxon(a, b)
    return {"statistic": float(stat), "pvalue": float(p)}


def holm_bonferroni(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values within a pre-registered family."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted: dict[str, float] = {}
    running_max = 0.0
    for i, (name, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running_max = max(running_max, adj)  # enforce monotonicity
        adjusted[name] = running_max
    return adjusted
