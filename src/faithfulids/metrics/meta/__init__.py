"""metrics.meta — RQ0 meta-validation (sensitivity/specificity/ROC vs corruption)."""

from __future__ import annotations

from faithfulids.metrics.meta.validation import (
    fluency_correlation,
    roc_auc,
    sensitivity_specificity,
)

__all__ = ["sensitivity_specificity", "roc_auc", "fluency_correlation"]
