"""Layer-2 saturation diagnostic (L4).

Is comprehensiveness ≈ 0 because the erasure is a no-op (a wiring bug), or because
probability space *saturates* on a near-certain detector (p≈0.999 → 0.994 reads as
Δ≈0)? This recomputes ε_att and ε_model comprehensiveness/sufficiency in BOTH
probability and margin (log-odds) space over a set of instances and summarises how
much signal probability space hides.

It receives a frozen detector, attributions, and per-instance claims as arguments
(imports no generation, no orchestration); the pure summary is unit-tested
offline. The heavy data/detector wiring lives in
``tools/layer2_saturation_diagnostic.py`` and runs in the pinned env over a pilot
run's re-derived inputs. Pair this with the erasure-efficacy smoke test: the smoke
test rules out a no-op erasure; this quantifies saturation given a working one.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from faithfulids.framework import (
    AttributionArtifact,
    ClaimSet,
    DetectorArtifact,
    ErasureOperator,
)
from faithfulids.metrics.layer2.metrics import (
    comprehensiveness,
    comprehensiveness_cited,
    sufficiency,
    sufficiency_cited,
)

_ZERO = 1e-9


def _summary(prob: Sequence[float], margin: Sequence[float]) -> dict[str, Any]:
    n = len(prob)
    if n == 0:
        return {"n": 0}
    mean_abs_prob = sum(abs(x) for x in prob) / n
    mean_abs_margin = sum(abs(x) for x in margin) / n
    return {
        "n": n,
        "mean_abs_prob": mean_abs_prob,
        "mean_abs_margin": mean_abs_margin,
        "frac_zero_prob": sum(1 for x in prob if abs(x) <= _ZERO) / n,
        "frac_zero_margin": sum(1 for x in margin if abs(x) <= _ZERO) / n,
        # how much larger the margin-space signal is (the saturation factor); None
        # when prob space is flat-zero, which by itself signals saturation.
        "margin_over_prob": (mean_abs_margin / mean_abs_prob) if mean_abs_prob > _ZERO else None,
    }


def saturation_report(
    detector: DetectorArtifact,
    instances: Mapping[str, Mapping[str, float]],
    attributions: Mapping[str, AttributionArtifact],
    claims_map: Mapping[tuple[str, str], ClaimSet],
    erasure: ErasureOperator,
    *,
    k_values: Sequence[int],
) -> dict[str, dict[str, Any]]:
    """Per-(metric, k) prob-vs-margin summaries.

    ``instances``: {instance_id: feature dict}. ``attributions``: {instance_id:
    AttributionArtifact}. ``claims_map``: {(instance_id, generator_id): ClaimSet}.
    """
    out: dict[str, dict[str, Any]] = {}

    # ε_att (attribution-driven, generator-blind): one value per instance.
    for k in k_values:
        for name, fn in (("comprehensiveness", comprehensiveness), ("sufficiency", sufficiency)):
            prob, margin = [], []
            for iid, inst in instances.items():
                attr = attributions[iid]
                prob.append(fn(attr, detector, inst, erasure, k=k, delta_space="prob"))
                margin.append(fn(attr, detector, inst, erasure, k=k, delta_space="margin"))
            out[f"eps_att.{name}.k{k}"] = _summary(prob, margin)

    # ε_model (claim-driven): one value per (instance, generator).
    for k in k_values:
        for name, fn in (
            ("comprehensiveness_cited", comprehensiveness_cited),
            ("sufficiency_cited", sufficiency_cited),
        ):
            prob, margin = [], []
            for (iid, _gid), claims in claims_map.items():
                inst = instances[iid]
                prob.append(fn(claims, detector, inst, erasure, k=k, delta_space="prob"))
                margin.append(fn(claims, detector, inst, erasure, k=k, delta_space="margin"))
            out[f"eps_model.{name}.k{k}"] = _summary(prob, margin)

    return out
