"""attribution — L2.

A common ``AttributionArtifact`` produced by exact TreeSHAP or approximate
DeepSHAP, with a content-addressed cache. Concrete attributors are imported
lazily by method (``get_attributor``) so this package never pulls in
``shap`` / ``torch`` unless used. ``attribution`` and ``detectors`` are
independent L2 siblings and must not import each other.
"""

from __future__ import annotations

from faithfulids.attribution.base import (
    ATTRIBUTION_MODULES,
    AttributionCache,
    attribution_cache_key,
    get_attributor,
)

__all__ = [
    "AttributionCache",
    "attribution_cache_key",
    "get_attributor",
    "ATTRIBUTION_MODULES",
]
