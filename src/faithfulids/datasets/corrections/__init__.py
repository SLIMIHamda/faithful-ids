"""datasets.corrections — the versioned Engelen/Lanvin fix-set (L1)."""

from __future__ import annotations

from faithfulids.datasets.corrections.base import (
    CorrectionRule,
    TodoCorrection,
    UnimplementedCorrection,
)
from faithfulids.datasets.corrections.engelen_lanvin import (
    PIPELINE_VERSION,
    build_pipeline,
)
from faithfulids.datasets.corrections.pipeline import (
    ChecksumMismatch,
    CorrectionPipeline,
    dataframe_sha256,
)

__all__ = [
    "CorrectionRule",
    "TodoCorrection",
    "UnimplementedCorrection",
    "CorrectionPipeline",
    "ChecksumMismatch",
    "dataframe_sha256",
    "PIPELINE_VERSION",
    "build_pipeline",
]
