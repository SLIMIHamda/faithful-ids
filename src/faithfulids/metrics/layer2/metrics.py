"""Layer-2 erasure-based faithfulness metrics (L4).

Two families, both measured on the frozen detector under an erasure operator:

* **ε_att (attribution-driven, claim-free)** — comprehensiveness / sufficiency of
  the *attribution's* top-k features. It never sees claims, so it probes whether
  the attribution φ picks the features the model actually uses (φ ↔ f). Emitted
  once per instance; generator-independent. ``comprehensiveness`` / ``sufficiency``.
* **ε_model (claim-driven)** — comprehensiveness / sufficiency of the features an
  explanation actually *cites* (S = top-k claimed features). It receives the
  extracted :class:`ClaimSet` (a legal metric input — see
  :mod:`faithfulids.framework.interfaces`) but **never** generator identity, so
  it stays generator-blind *by type* while being claim-aware. This is the
  per-explanation ε_model term of the decomposition
  (:mod:`faithfulids.framework.decomposition`): the gap between an explanation's
  claims and the model's true behaviour, measured directly *without routing
  through φ*. ``comprehensiveness_cited`` / ``sufficiency_cited``.

Both families are ERASER-style at k ∈ {1,3,5}. The score delta is taken in
probability space (default) or margin / log-odds space
(``delta_space="margin"``); margin avoids saturation when the detector is
near-certain (p≈0.999) and requires the detector to expose ``predict_margin``.
Formula versions live in ``configs/metrics/layer2_erasure.yaml``.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from faithfulids.framework import (
    AttributionArtifact,
    ClaimSet,
    DetectorArtifact,
    ErasureOperator,
    MetricSpec,
)

FORMULA_VERSION = "1.1.0"  # 1.1.0: add claim-driven ε_model family (additive; ε_att unchanged)


def _detector_score(
    detector: DetectorArtifact, rows: Sequence[Mapping[str, float]], delta_space: str
) -> list[float]:
    """Attack-class score per row, in probability or margin (log-odds) space."""
    if delta_space == "prob":
        return [float(x) for x in detector.predict_proba(rows)]
    if delta_space == "margin":
        fn = getattr(detector, "predict_margin", None)
        if fn is None:
            raise ValueError(
                "delta_space='margin' requires the detector to expose predict_margin; "
                "this frozen detector does not."
            )
        return [float(x) for x in fn(rows)]
    raise ValueError(f"unknown delta_space {delta_space!r} (expected 'prob' or 'margin')")


def _cited_topk(claims: ClaimSet, detector: DetectorArtifact, k: int) -> list[str]:
    """Top-k *erasable* cited features from a claim set (S).

    Ordered by claim rank (1 = most important) with unranked claims following in
    claim order; de-duplicated; intersected with the detector's feature space —
    a hallucinated feature cannot be erased, so it is captured by Layer-1 HFR /
    the Pass-B claim-hallucination metric, not here. At most ``k`` features.
    """
    ordered = sorted(
        claims.claims, key=lambda c: (c.rank is None, c.rank if c.rank is not None else 0)
    )
    known = set(detector.feature_names)
    out: list[str] = []
    for c in ordered:
        if c.feature in known and c.feature not in out:
            out.append(c.feature)
        if len(out) >= k:
            break
    return out


# --------------------------------------------------------------------------- #
# ε_att — attribution-driven, claim-free (the original Layer-2). Generator-blind.
# --------------------------------------------------------------------------- #
def comprehensiveness(
    attribution: AttributionArtifact,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> float:
    """ε_att: drop in attack score when the top-k *attributed* features are erased.

    High ⇒ the attribution's named features really drove the decision (φ ↔ f).
    """
    topk = list(attribution.ranked_features(k))
    s_full, s_erased = _detector_score(
        detector, [dict(instance), erasure.erase(instance, topk)], delta_space
    )
    return s_full - s_erased


def sufficiency(
    attribution: AttributionArtifact,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> float:
    """ε_att: drop in attack score when only the top-k *attributed* features are kept.

    Low ⇒ the attribution's named features alone reproduce the score.
    """
    topk = set(attribution.ranked_features(k))
    to_remove = [f for f in attribution.feature_names if f not in topk]
    s_full, s_kept = _detector_score(
        detector, [dict(instance), erasure.erase(instance, to_remove)], delta_space
    )
    return s_full - s_kept


# --------------------------------------------------------------------------- #
# ε_model — claim-driven. Receives the ClaimSet (legal), never generator identity.
# --------------------------------------------------------------------------- #
def comprehensiveness_cited(
    claims: ClaimSet,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> float:
    """ε_model: drop in attack score when the top-k *cited* features (S) are erased.

    High ⇒ the features the explanation actually names drove the decision
    (claims ↔ f). An explanation that cites no real feature scores 0 — it removes
    nothing decision-relevant, i.e. it is maximally unfaithful to the model here.
    """
    s = _cited_topk(claims, detector, k)
    s_full, s_erased = _detector_score(
        detector, [dict(instance), erasure.erase(instance, s)], delta_space
    )
    return s_full - s_erased


def sufficiency_cited(
    claims: ClaimSet,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> float:
    """ε_model: drop in attack score when only the top-k *cited* features are kept."""
    s = set(_cited_topk(claims, detector, k))
    to_remove = [f for f in detector.feature_names if f not in s]
    s_full, s_kept = _detector_score(
        detector, [dict(instance), erasure.erase(instance, to_remove)], delta_space
    )
    return s_full - s_kept


#: ε_att family (attribution-driven, claim-free).
EPS_ATT_METRICS = {
    "comprehensiveness": (comprehensiveness, MetricSpec("comprehensiveness", "layer2", FORMULA_VERSION)),
    "sufficiency": (sufficiency, MetricSpec("sufficiency", "layer2", FORMULA_VERSION)),
}

#: ε_model family (claim-driven).
EPS_MODEL_METRICS = {
    "comprehensiveness_cited": (
        comprehensiveness_cited,
        MetricSpec("comprehensiveness_cited", "layer2", FORMULA_VERSION),
    ),
    "sufficiency_cited": (
        sufficiency_cited,
        MetricSpec("sufficiency_cited", "layer2", FORMULA_VERSION),
    ),
}

#: Backward-compatible alias: the historical Layer-2 metrics are the ε_att family.
LAYER2_METRICS = EPS_ATT_METRICS


def compute_all(
    attribution: AttributionArtifact,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> dict[str, float]:
    """ε_att (attribution-driven) comprehensiveness + sufficiency for one instance."""
    return {
        name: fn(attribution, detector, instance, erasure, k=k, delta_space=delta_space)
        for name, (fn, _spec) in EPS_ATT_METRICS.items()
    }


def compute_eps_model(
    claims: ClaimSet,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> dict[str, float]:
    """ε_model (claim-driven) comprehensiveness + sufficiency for one explanation."""
    return {
        name: fn(claims, detector, instance, erasure, k=k, delta_space=delta_space)
        for name, (fn, _spec) in EPS_MODEL_METRICS.items()
    }
