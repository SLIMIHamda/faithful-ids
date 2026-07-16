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
    attack_probability,
)

FORMULA_VERSION = "1.1.0"  # ε_att + ε_model *_cited. 1.2.0 (file): add |S|-normalised *_per_feature (additive)


def _detector_score(
    detector: DetectorArtifact,
    rows: Sequence[Mapping[str, float]],
    delta_space: str,
    target_class: str,
) -> list[float]:
    """Score of ``target_class`` per row, in probability or margin (log-odds) space.

    The caller PINS ``target_class`` from the unerased instance and reuses it for
    every erased variant (queue #5.4): erasure can flip the argmax, and a delta
    taken across two DIFFERENT classes measures nothing.
    """
    names = tuple(detector.class_names)
    if target_class not in names:
        raise ValueError(f"target class {target_class!r} is not one of {names}")
    c = names.index(target_class)
    if delta_space == "prob":
        return [float(row[c]) for row in detector.predict_proba(rows)]
    if delta_space == "margin":
        fn = getattr(detector, "predict_margin", None)
        if fn is None:
            raise ValueError(
                "delta_space='margin' requires the detector to expose predict_margin; "
                "this frozen detector does not."
            )
        return [float(row[c]) for row in fn(rows)]
    raise ValueError(f"unknown delta_space {delta_space!r} (expected 'prob' or 'margin')")


def _target_class(
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    explained_class: str | None = None,
) -> str:
    """The class Layer-2 measures — the class the ATTRIBUTION explains (queue #5.4).

    An erasure delta is only interpretable against the same class the attribution
    is about, so this mirrors the #5.3 selection rule:

    * **binary** — the attribution explains the positive/attack side for every
      instance (benign rows included), so Layer-2 measures that side. This is the
      pilot's established semantics, deliberately unchanged.
    * **multi-class** — the attribution explains the class the detector predicted
      on the FULL instance; ``explained_class`` (stamped on the artifact by #5.3b)
      is used when available, else it is recomputed from the unerased instance.
    """
    names = tuple(detector.class_names)
    if len(names) == 2:
        return names[-1]
    if explained_class is not None:
        return explained_class
    return detector.predicted_class([dict(instance)])[0]


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
    target = _target_class(detector, instance, attribution.explained_class)
    s_full, s_erased = _detector_score(
        detector, [dict(instance), erasure.erase(instance, topk)], delta_space, target
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
    target = _target_class(detector, instance, attribution.explained_class)
    s_full, s_kept = _detector_score(
        detector, [dict(instance), erasure.erase(instance, to_remove)], delta_space, target
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
    target = _target_class(detector, instance)
    s_full, s_erased = _detector_score(
        detector, [dict(instance), erasure.erase(instance, s)], delta_space, target
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
    target = _target_class(detector, instance)
    s_full, s_kept = _detector_score(
        detector, [dict(instance), erasure.erase(instance, to_remove)], delta_space, target
    )
    return s_full - s_kept


#: ε_att family (attribution-driven, claim-free).
EPS_ATT_METRICS = {
    "comprehensiveness": (comprehensiveness, MetricSpec("comprehensiveness", "layer2", FORMULA_VERSION)),
    "sufficiency": (sufficiency, MetricSpec("sufficiency", "layer2", FORMULA_VERSION)),
}

def comprehensiveness_cited_per_feature(
    claims: ClaimSet,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> float:
    """ε_model comprehensiveness **normalised by the cited-set size |S|**.

    Raw ``comprehensiveness_cited@k`` erases ``min(k, |S ∩ known|)`` features, but
    generators cite different numbers of features (a verifier-pruned B4 cites
    fewer than B0's fixed top-k), so the raw ``@k`` value conflates set size with
    per-feature potency — which is why an aggressively-pruned generator can post a
    larger raw drop than the SHAP baseline. Dividing by |S| gives **decision mass
    removed per cited feature**, comparable across generators regardless of how
    many each names. ``|S| = 0`` (cites nothing erasable) → ``0.0``.
    """
    s = _cited_topk(claims, detector, k)
    if not s:
        return 0.0
    target = _target_class(detector, instance)
    s_full, s_erased = _detector_score(
        detector, [dict(instance), erasure.erase(instance, s)], delta_space, target
    )
    return (s_full - s_erased) / len(s)


def sufficiency_cited_per_feature(
    claims: ClaimSet,
    detector: DetectorArtifact,
    instance: Mapping[str, float],
    erasure: ErasureOperator,
    *,
    k: int,
    delta_space: str = "prob",
) -> float:
    """ε_model sufficiency normalised by |S| (see :func:`comprehensiveness_cited_per_feature`)."""
    s = _cited_topk(claims, detector, k)
    if not s:
        return 0.0
    keep = set(s)
    to_remove = [f for f in detector.feature_names if f not in keep]
    target = _target_class(detector, instance)
    s_full, s_kept = _detector_score(
        detector, [dict(instance), erasure.erase(instance, to_remove)], delta_space, target
    )
    return (s_full - s_kept) / len(s)


# ``_per_feature`` variants are new metrics (own version), so the historical
# ``*_cited`` stamps are unchanged; the family/file version bumps to 1.2.0.
_PER_FEATURE_VERSION = "1.0.0"

#: ε_model family (claim-driven). ``*_per_feature`` normalise by |S| (cited-set
#: size), removing the set-size confound in cross-generator comparison.
EPS_MODEL_METRICS = {
    "comprehensiveness_cited": (
        comprehensiveness_cited,
        MetricSpec("comprehensiveness_cited", "layer2", FORMULA_VERSION),
    ),
    "sufficiency_cited": (
        sufficiency_cited,
        MetricSpec("sufficiency_cited", "layer2", FORMULA_VERSION),
    ),
    "comprehensiveness_cited_per_feature": (
        comprehensiveness_cited_per_feature,
        MetricSpec("comprehensiveness_cited_per_feature", "layer2", _PER_FEATURE_VERSION),
    ),
    "sufficiency_cited_per_feature": (
        sufficiency_cited_per_feature,
        MetricSpec("sufficiency_cited_per_feature", "layer2", _PER_FEATURE_VERSION),
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
