"""The Engelen/Lanvin CICIDS2017 correction fix-set (L1).

Encodes the *structure* of the published corrections as an ordered list of
versioned rules. Each rule's exact logic is a TODO that hard-fails if executed
(:class:`TodoCorrection`) — the pipeline shape, ordering, versioning, and
provenance are real and tested now; the numeric fix logic is filled in per rule
without changing the pipeline contract.

References (to implement against, not restated as parameters here):
- G. Engelen et al., "Troubleshooting an Intrusion Detection Dataset: the
  CICIDS2017 Case Study."
- M. Lanvin et al., "Errors in the CICIDS2017 Dataset and the Corrected Version."
"""

from __future__ import annotations

from faithfulids.datasets.corrections.base import TodoCorrection
from faithfulids.datasets.corrections.pipeline import CorrectionPipeline

#: Pipeline version — MUST match configs/datasets/cicids2017_corrected.yaml
#: correction.pipeline_version. A change here is a new corrected corpus.
PIPELINE_VERSION = "1.0.0"

_RULES = [
    TodoCorrection(
        "drop_duplicate_flows", "1.0.0",
        "Remove exact-duplicate flow records introduced by the flow exporter.",
    ),
    TodoCorrection(
        "repair_label_leakage", "1.0.0",
        "Fix mislabelled BENIGN/attack rows around attack-window boundaries.",
    ),
    TodoCorrection(
        "handle_nan_inf", "1.0.0",
        "Resolve NaN/Inf in rate features (e.g. Flow Bytes/s) per the corrected spec.",
    ),
    TodoCorrection(
        "fix_attack_window_timestamps", "1.0.0",
        "Correct attack-window timestamp misalignment affecting class assignment.",
    ),
    TodoCorrection(
        "canonicalise_feature_names", "1.0.0",
        "Normalise feature-name whitespace/casing to the canonical vocabulary.",
    ),
]


def build_pipeline() -> CorrectionPipeline:
    """The Engelen/Lanvin correction pipeline for CICIDS2017."""
    return CorrectionPipeline(version=PIPELINE_VERSION, rules=_RULES)
