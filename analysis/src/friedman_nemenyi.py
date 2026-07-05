"""Friedman omnibus + Nemenyi post-hoc with critical-difference geometry.

Pure consumer of numeric matrices (methods x blocks). Imports no faithfulids
execution code — statistics can never rerun experiments (edge 4).
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from scipy.stats import friedmanchisquare

# Nemenyi critical values q_alpha (alpha=0.05) indexed by number of methods k.
# (Studentized range / sqrt(2); standard tabulated values.)
_Q05 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031,
        9: 3.102, 10: 3.164}


def average_ranks(scores: np.ndarray, *, higher_is_better: bool = True) -> np.ndarray:
    """Average ranks per method across blocks (rank 1 = best)."""
    x = np.asarray(scores, dtype=float)
    if higher_is_better:
        x = -x
    # rank within each block (column), averaging ties
    n_methods, n_blocks = x.shape
    ranks = np.zeros_like(x)
    for b in range(n_blocks):
        col = x[:, b]
        order = np.argsort(col, kind="mergesort")
        r = np.empty(n_methods, dtype=float)
        i = 0
        while i < n_methods:
            j = i
            while j + 1 < n_methods and col[order[j + 1]] == col[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for m in range(i, j + 1):
                r[order[m]] = avg
            i = j + 1
        ranks[:, b] = r
    return ranks.mean(axis=1)


def critical_difference(k: int, n_blocks: int, alpha: float = 0.05) -> float:
    """Nemenyi critical difference for k methods over n_blocks (alpha=0.05)."""
    if alpha != 0.05:
        raise ValueError("only alpha=0.05 is tabulated here (pre-registered)")
    if k not in _Q05:
        raise ValueError(f"no tabulated q for k={k}")
    q = _Q05[k]
    return q * math.sqrt(k * (k + 1) / (6.0 * n_blocks))


def friedman_nemenyi(
    scores: Sequence[Sequence[float]], *, higher_is_better: bool = True, alpha: float = 0.05
) -> dict:
    """Run Friedman + Nemenyi. ``scores`` is methods x blocks."""
    x = np.asarray(scores, dtype=float)
    k, n_blocks = x.shape
    stat, p = friedmanchisquare(*[x[i, :] for i in range(k)])
    ranks = average_ranks(x, higher_is_better=higher_is_better)
    cd = critical_difference(k, n_blocks, alpha)
    return {
        "statistic": float(stat),
        "pvalue": float(p),
        "avg_ranks": ranks.tolist(),
        "critical_difference": cd,
        "n_methods": k,
        "n_blocks": n_blocks,
    }
