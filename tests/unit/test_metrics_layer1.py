"""Layer-1 metrics vs the hand-computed fixture (the RQ0 analogue for unit tests)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from faithfulids.framework import AttributionArtifact, ClaimSet
from faithfulids.metrics.layer1 import compute_all

FIXTURE = Path(__file__).resolve().parents[1] / "metrics_fixtures" / "layer1_basic.json"


def test_layer1_matches_hand_computed_fixture():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    attribution = AttributionArtifact.from_dict(fx["attribution"])
    claims = ClaimSet.from_dict(fx["claims"])
    got = compute_all(claims, attribution, top_k=fx["top_k"])
    for name, expected in fx["expected"].items():
        assert got[name] == pytest.approx(expected), f"{name}: {got[name]} != {expected}"


def test_unrecorded_evidence_counts_as_asserted():
    """RQ0 guarantee: corruption-built claims carry direction_evidence=None and
    MUST stay inside dsa_asserted's denominator — a sign-flip corruption may not
    escape the confirmatory metric by being 'unasserted'."""
    from faithfulids.framework import ClaimTuple, Direction
    from faithfulids.metrics.layer1 import dsa_asserted, direction_assertion_rate

    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    attribution = AttributionArtifact.from_dict(fx["attribution"])
    flipped = ClaimSet(
        instance_id="i0",
        claims=(ClaimTuple(feature="A", direction=Direction.NEGATIVE),),  # attr A is +
        extractor_id="eval_extractor",
        extractor_version="1.0.0",
        prompt_sha256="a" * 64,
    )
    assert direction_assertion_rate(flipped, attribution) == 1.0
    assert dsa_asserted(flipped, attribution) == 0.0  # the flip IS caught


def test_layer1_signature_has_no_generator_identity():
    """Generator-blindness by type: the metric callables accept only claims,
    attribution, and top_k — never a generator id."""
    import inspect

    from faithfulids.metrics.layer1 import LAYER1_METRICS

    for _name, (fn, _spec) in LAYER1_METRICS.items():
        params = set(inspect.signature(fn).parameters)
        assert "generator" not in params and "generator_id" not in params
