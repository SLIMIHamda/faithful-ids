"""corruption — L3, the RQ0 operators.

Six deterministic operators over faithful claim sets, emitting ground-truth
"corrupted" labels for meta-validation (EXP-G-002). Consumes framework types
only; never imports ``generation``.
"""

from __future__ import annotations

from faithfulids.corruption.operators import (
    OPERATORS,
    CorruptionResult,
    apply_operator,
)

__all__ = ["OPERATORS", "CorruptionResult", "apply_operator"]
