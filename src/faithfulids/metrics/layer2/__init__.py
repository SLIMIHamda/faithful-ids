"""metrics.layer2 — erasure-based faithfulness (comprehensiveness/sufficiency)."""

from __future__ import annotations

from faithfulids.metrics.layer2.erasure import (
    ConditionalExpectationImputer,
    SimpleBackgroundErasure,
)
from faithfulids.metrics.layer2.metrics import (
    EPS_ATT_METRICS,
    EPS_MODEL_METRICS,
    FORMULA_VERSION,
    LAYER2_METRICS,
    comprehensiveness,
    comprehensiveness_cited,
    comprehensiveness_cited_per_feature,
    compute_all,
    compute_eps_model,
    sufficiency,
    sufficiency_cited,
    sufficiency_cited_per_feature,
)

__all__ = [
    "FORMULA_VERSION",
    "LAYER2_METRICS",
    "EPS_ATT_METRICS",
    "EPS_MODEL_METRICS",
    "comprehensiveness",
    "sufficiency",
    "comprehensiveness_cited",
    "sufficiency_cited",
    "comprehensiveness_cited_per_feature",
    "sufficiency_cited_per_feature",
    "compute_all",
    "compute_eps_model",
    "SimpleBackgroundErasure",
    "ConditionalExpectationImputer",
]
