"""metrics.layer2 — erasure-based faithfulness (comprehensiveness/sufficiency)."""

from __future__ import annotations

from faithfulids.metrics.layer2.erasure import (
    ConditionalExpectationImputer,
    SimpleBackgroundErasure,
)
from faithfulids.metrics.layer2.metrics import (
    FORMULA_VERSION,
    LAYER2_METRICS,
    comprehensiveness,
    compute_all,
    sufficiency,
)

__all__ = [
    "FORMULA_VERSION",
    "LAYER2_METRICS",
    "comprehensiveness",
    "sufficiency",
    "compute_all",
    "SimpleBackgroundErasure",
    "ConditionalExpectationImputer",
]
