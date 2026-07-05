"""Bootstrap 95% CIs + effect sizes on headline numbers (seeded, reproducible)."""

from __future__ import annotations

from typing import Sequence

import numpy as np


def bootstrap_mean_ci(
    values: Sequence[float], *, n_resamples: int = 10000, ci: float = 0.95, seed: int = 0
) -> dict:
    x = np.asarray(values, dtype=float)
    rng = np.random.RandomState(seed)  # seed from the seed table (reproducible)
    means = np.array([rng.choice(x, size=len(x), replace=True).mean() for _ in range(n_resamples)])
    lo = float(np.percentile(means, (1 - ci) / 2 * 100))
    hi = float(np.percentile(means, (1 + ci) / 2 * 100))
    return {"mean": float(x.mean()), "ci_low": lo, "ci_high": hi, "ci": ci, "n_resamples": n_resamples}


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Paired-difference Cohen's d (effect size)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    diff = a - b
    sd = diff.std(ddof=1)
    return float(diff.mean() / sd) if sd > 0 else 0.0
