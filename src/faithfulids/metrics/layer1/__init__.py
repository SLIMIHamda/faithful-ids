"""metrics.layer1 — claim-level faithfulness (P/R/F1, DSA, ARC, HFR)."""

from __future__ import annotations

from faithfulids.metrics.layer1.metrics import (
    FORMULA_VERSION,
    LAYER1_METRICS,
    arc,
    arc_n_pairs,
    compute_all,
    direction_assertion_rate,
    dsa,
    dsa_asserted,
    hfr,
    mention_f1,
    mention_precision,
    mention_recall,
)

__all__ = [
    "FORMULA_VERSION",
    "LAYER1_METRICS",
    "compute_all",
    "mention_precision",
    "mention_recall",
    "mention_f1",
    "dsa",
    "dsa_asserted",
    "direction_assertion_rate",
    "arc",
    "arc_n_pairs",
    "hfr",
]
