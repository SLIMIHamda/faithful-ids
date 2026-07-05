"""Coverage-risk curves + AURC for B4 abstention (firewall rule 3).

A mandatory output of every B4 cell: as the abstention threshold varies, plot
selective risk against coverage and integrate the area under the risk-coverage
curve (AURC). On abstention the fallback degrades to B1 (never silence).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np


def risk_coverage_curve(risks: Sequence[float], confidences: Sequence[float]) -> dict:
    """Selective risk vs coverage, ordered by descending confidence.

    ``risks[i]`` is the per-instance error (e.g. 1 - faithfulness) and
    ``confidences[i]`` the verifier confidence used to decide abstention.
    """
    r = np.asarray(risks, dtype=float)
    c = np.asarray(confidences, dtype=float)
    order = np.argsort(-c, kind="mergesort")  # most confident first
    r_sorted = r[order]
    n = len(r_sorted)
    coverages, selective_risks = [], []
    cum = 0.0
    for i in range(n):
        cum += r_sorted[i]
        coverages.append((i + 1) / n)
        selective_risks.append(cum / (i + 1))
    aurc = float(
        sum(
            (coverages[i] - coverages[i - 1]) * (selective_risks[i] + selective_risks[i - 1]) / 2.0
            for i in range(1, len(coverages))
        )
    )
    return {
        "coverage": coverages,
        "selective_risk": selective_risks,
        "aurc": aurc,
        "n": n,
    }
