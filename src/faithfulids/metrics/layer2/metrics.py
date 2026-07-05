"""Layer-2 erasure-based faithfulness metrics (L4).

ERASER-style comprehensiveness and sufficiency at k ∈ {1,3,5}, measured on the
detector's output under an erasure operator. **Generator-blind, and claim-free**
— Layer-2 probes the model's behaviour directly, independent of any narration.
Formula versions live in ``configs/metrics/layer2_erasure.yaml``.
"""

from __future__ import annotations

from typing import Mapping

from faithfulids.framework import AttributionArtifact, DetectorArtifact, ErasureOperator, MetricSpec

FORMULA_VERSION = "1.0.0"


def comprehensiveness(
    attribution: AttributionArtifact,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
) -> float:
    """Drop in attack score when the top-k attributed features are erased.

    High comprehensiveness ⇒ the named features really drove the decision.
    """
    topk = list(attribution.ranked_features(k))
    p_full = float(detector.predict_proba([dict(instance)])[0])
    erased = erasure.erase(instance, topk)
    p_erased = float(detector.predict_proba([erased])[0])
    return p_full - p_erased


def sufficiency(
    attribution: AttributionArtifact,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
) -> float:
    """Drop in attack score when only the top-k features are kept (rest erased).

    Low sufficiency ⇒ the named features alone are enough to reproduce the score.
    """
    topk = set(attribution.ranked_features(k))
    to_remove = [f for f in attribution.feature_names if f not in topk]
    p_full = float(detector.predict_proba([dict(instance)])[0])
    kept = erasure.erase(instance, to_remove)
    p_kept = float(detector.predict_proba([kept])[0])
    return p_full - p_kept


LAYER2_METRICS = {
    "comprehensiveness": (comprehensiveness, MetricSpec("comprehensiveness", "layer2", FORMULA_VERSION)),
    "sufficiency": (sufficiency, MetricSpec("sufficiency", "layer2", FORMULA_VERSION)),
}


def compute_all(
    attribution: AttributionArtifact,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
) -> dict[str, float]:
    return {
        name: fn(attribution, detector, instance, erasure, k=k)
        for name, (fn, _spec) in LAYER2_METRICS.items()
    }
