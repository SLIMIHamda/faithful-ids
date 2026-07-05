"""Variance components (instance, generation, extraction) as random effects.

A moment-based decomposition of total variance into the pre-registered random
effects. For the full mixed-effects model see ``mixed_effects.py``; this gives
the headline variance-share breakdown.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np


def variance_shares(values: Sequence[float], factors: dict[str, Sequence]) -> dict[str, float]:
    """Share of total variance associated with each grouping factor.

    For each factor, the between-group variance of group means (a lower-bound
    moment estimate of that random effect's variance contribution) is expressed
    as a fraction of the total variance. Residual is 1 - sum(shares) (clamped).
    """
    x = np.asarray(values, dtype=float)
    total = x.var(ddof=0)
    shares: dict[str, float] = {}
    if total == 0:
        return {name: 0.0 for name in factors} | {"residual": 1.0}
    for name, labels in factors.items():
        labels = np.asarray(list(labels))
        group_means = []
        weights = []
        for lvl in np.unique(labels):
            mask = labels == lvl
            group_means.append(x[mask].mean())
            weights.append(mask.sum())
        gm = np.asarray(group_means)
        w = np.asarray(weights, dtype=float)
        between = np.average((gm - x.mean()) ** 2, weights=w)
        shares[name] = float(min(1.0, between / total))
    shares["residual"] = float(max(0.0, 1.0 - sum(shares.values())))
    return shares
