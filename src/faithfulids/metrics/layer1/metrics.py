"""Layer-1 claim-level faithfulness metrics (L4).

Over extracted claim tuples vs the ground-truth attribution:

* feature-mention precision / recall / F1
* DSA — Directional Sign Agreement
* ARC — Attribution Rank Correlation (Spearman)
* HFR — Hallucinated-Feature Rate

**Generator-blind by type.** Every function takes only ``(claims, attribution)``
(+ ``top_k``); none can receive generator identity (framework edge). Formula
versions live in ``configs/metrics/layer1.yaml``.
"""

from __future__ import annotations

from faithfulids.framework import AttributionArtifact, ClaimSet, Direction, MetricSpec

FORMULA_VERSION = "1.0.0"  # mention_* / arc / hfr — unchanged
# 1.1.0 (file): add dsa_asserted + direction_assertion_rate (additive) — splits
# reading fidelity from assertion style via the direction_evidence stamp
# (2026-07-11 audit follow-up).
# 1.2.0 (directional): dsa / dsa_asserted / direction_assertion_rate now score
# only claims about the attribution's TOP-K features (2026-07-14). Previously
# they graded EVERY claimed feature present in the attribution, so a claim about
# a bottom-of-vocab feature was checked against a near-zero SHAP value whose sign
# is numerical noise — inflating/deflating DSA with meaningless matches. Bounding
# to top-k mirrors the mention metrics and confines directional agreement to the
# region where the sign is real. dsa jumps 1.0.0->1.2.0 (skips 1.1.0) so all three
# directional metrics share one version. Run-level means of dsa_asserted must
# additionally EXCLUDE no-assertion instances (direction_assertion_rate == 0),
# where the metric is undefined and returns a structural 0.0 — see analysis.run.
_DIRECTIONAL_VERSION = "1.2.0"


def _reference_topk(attribution: AttributionArtifact, top_k: int | None) -> list[str]:
    return list(attribution.ranked_features(top_k))


def _present_topk(claims: ClaimSet, attribution: AttributionArtifact, top_k: int | None) -> list:
    """Claims whose feature is in the attribution's top-k reference set — the
    domain of the directional metrics. ``top_k=None`` falls back to all attributed
    features (so ``sign_of`` is always defined and pre-top-k callers are unchanged)."""
    ref = set(_reference_topk(attribution, top_k))
    return [c for c in claims.claims if c.feature in ref]


def _claimed_features(claims: ClaimSet) -> list[str]:
    return [c.feature for c in claims.claims]


def mention_precision(claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None) -> float:
    claimed = _claimed_features(claims)
    if not claimed:
        return 0.0
    ref = set(_reference_topk(attribution, top_k))
    hit = sum(1 for f in claimed if f in ref)
    return hit / len(claimed)


def mention_recall(claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None) -> float:
    ref = _reference_topk(attribution, top_k)
    if not ref:
        return 0.0
    claimed = set(_claimed_features(claims))
    hit = sum(1 for f in ref if f in claimed)
    return hit / len(ref)


def mention_f1(claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None) -> float:
    p = mention_precision(claims, attribution, top_k=top_k)
    r = mention_recall(claims, attribution, top_k=top_k)
    return 0.0 if (p + r) == 0 else 2 * p * r / (p + r)


def dsa(claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None) -> float:
    """Fraction of claimed top-k features whose claimed direction matches the
    attribution's sign.

    Restricted to the attribution's top-k features (out-of-top-k SHAP signs are
    noise). Includes extractor-DEFAULTED directions (no textual evidence), so for
    generators that often assert no direction this blends reading fidelity with
    the default-vs-base-rate coin flip. Kept for continuity/descriptive use;
    ``dsa_asserted`` is the confirmatory directional metric (2026-07-11 audit).
    """
    present = _present_topk(claims, attribution, top_k)
    if not present:
        return 0.0
    agree = sum(1 for c in present if c.direction is attribution.sign_of(c.feature))
    return agree / len(present)


def _asserted(
    claims: ClaimSet, attribution: AttributionArtifact, top_k: int | None
) -> tuple[list, list]:
    """(present-top-k, present-top-k-and-asserted) claims. A claim is *asserted*
    unless its ``direction_evidence`` is explicitly ``"default"`` — ``None``
    (legacy or corruption-built claims) counts as asserted so RQ0's sign-flip
    corruptions stay inside the ``dsa_asserted`` denominator and must be caught."""
    present = _present_topk(claims, attribution, top_k)
    return present, [c for c in present if c.direction_evidence != "default"]


def dsa_asserted(claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None) -> float:
    """DSA over top-k claims whose direction the text actually asserts (evidence
    = word / number / llm / unrecorded) — pure reading fidelity, no graded
    guesses. Returns a structural 0.0 when nothing is asserted, so its run-level
    mean MUST exclude those instances (gate on ``direction_assertion_rate > 0``,
    done in analysis.run) — otherwise no-assertion instances drag the confirmatory
    mean toward 0. Read it WITH ``direction_assertion_rate``, never alone."""
    _, asserted = _asserted(claims, attribution, top_k)
    if not asserted:
        return 0.0
    agree = sum(1 for c in asserted if c.direction is attribution.sign_of(c.feature))
    return agree / len(asserted)


def direction_assertion_rate(
    claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None
) -> float:
    """Fraction of present top-k claims whose direction is text-asserted rather
    than extractor-defaulted. A generator property (explanations that never commit
    to a direction are less useful to an analyst), and the coverage companion
    to ``dsa_asserted``: dsa ≈ dsa_asserted*rate + default_hits*(1-rate). Also the
    aggregation gate — ``rate > 0`` iff ``dsa_asserted`` is defined for the
    instance, so run-level means drop no-assertion instances by excluding rate==0."""
    present, asserted = _asserted(claims, attribution, top_k)
    if not present:
        return 0.0
    return len(asserted) / len(present)


def hfr(claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None) -> float:
    """Hallucinated-Feature Rate: claimed features absent from the attribution."""
    claimed = _claimed_features(claims)
    if not claimed:
        return 0.0
    known = set(attribution.feature_names)
    return sum(1 for f in claimed if f not in known) / len(claimed)


def _spearman(a: list[float], b: list[float]) -> float:
    """Spearman rank correlation (ties broken by input order; small-n)."""
    n = len(a)
    if n < 2:
        return 0.0

    def ranks(xs: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: xs[i])
        r = [0.0] * n
        for pos, i in enumerate(order):
            r[i] = float(pos)
        return r

    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((ra[i] - ma) ** 2 for i in range(n)) ** 0.5
    db = sum((rb[i] - mb) ** 2 for i in range(n)) ** 0.5
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def arc(claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None) -> float:
    """Attribution Rank Correlation: Spearman between claimed ranks and the
    attribution's ranks, over features that are claimed-with-rank and attributed."""
    ref_order = list(attribution.ranked_features(None))
    ref_rank = {f: i + 1 for i, f in enumerate(ref_order)}
    claimed_ranks: list[float] = []
    attr_ranks: list[float] = []
    for c in claims.claims:
        if c.rank is not None and c.feature in ref_rank:
            claimed_ranks.append(float(c.rank))
            attr_ranks.append(float(ref_rank[c.feature]))
    if len(claimed_ranks) < 2:
        return 0.0
    return _spearman(claimed_ranks, attr_ranks)


#: name -> (callable, MetricSpec)
LAYER1_METRICS = {
    "mention_precision": (mention_precision, MetricSpec("mention_precision", "layer1", FORMULA_VERSION)),
    "mention_recall": (mention_recall, MetricSpec("mention_recall", "layer1", FORMULA_VERSION)),
    "mention_f1": (mention_f1, MetricSpec("mention_f1", "layer1", FORMULA_VERSION)),
    "dsa": (dsa, MetricSpec("dsa", "layer1", _DIRECTIONAL_VERSION)),
    "dsa_asserted": (dsa_asserted, MetricSpec("dsa_asserted", "layer1", _DIRECTIONAL_VERSION)),
    "direction_assertion_rate": (
        direction_assertion_rate,
        MetricSpec("direction_assertion_rate", "layer1", _DIRECTIONAL_VERSION),
    ),
    "arc": (arc, MetricSpec("arc", "layer1", FORMULA_VERSION)),
    "hfr": (hfr, MetricSpec("hfr", "layer1", FORMULA_VERSION)),
}


def compute_all(
    claims: ClaimSet, attribution: AttributionArtifact, *, top_k: int | None = None
) -> dict[str, float]:
    """All Layer-1 metrics for one instance. No generator identity is accepted."""
    return {name: fn(claims, attribution, top_k=top_k) for name, (fn, _spec) in LAYER1_METRICS.items()}
