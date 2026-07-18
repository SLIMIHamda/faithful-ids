"""metrics.meta — RQ0 meta-validation (sensitivity/specificity/ROC vs corruption)."""

from __future__ import annotations

from faithfulids.metrics.meta.validation import (
    find_operating_point,
    fluency_correlation,
    roc_auc,
    sensitivity_specificity,
)

__all__ = ["sensitivity_specificity", "roc_auc", "find_operating_point", "fluency_correlation"]
