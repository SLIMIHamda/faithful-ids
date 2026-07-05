"""detectors — L2, the training/inference artifact boundary.

Family implementations are imported LAZILY (``get_trainer`` / ``load_frozen``),
so importing this package never pulls in ``xgboost`` or ``torch``. Training
writes frozen artifacts to ``models/``; inference loads them and can never
retrain (import-linter edge 6).
"""

from __future__ import annotations

from faithfulids.detectors.base import (
    DETECTOR_MODULES,
    FrozenDetector,
    get_trainer,
    load_frozen,
)

__all__ = ["FrozenDetector", "DETECTOR_MODULES", "get_trainer", "load_frozen"]
