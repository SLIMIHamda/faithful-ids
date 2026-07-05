"""Framework schema round-trips + JSON Schema conformance."""

from __future__ import annotations

import jsonschema
import pytest

from faithfulids.framework import (
    ATTRIBUTION_ARTIFACT_SCHEMA,
    CLAIM_SET_SCHEMA,
    CLAIM_TUPLE_SCHEMA,
    EXPLANATION_RECORD_SCHEMA,
    AttributionArtifact,
    ClaimSet,
    ClaimTuple,
    Direction,
    ExplanationRecord,
)


def test_direction_sign_and_roundtrip():
    assert Direction.POSITIVE.sign == 1
    assert Direction.NEGATIVE.sign == -1
    assert Direction.from_str("+") is Direction.POSITIVE
    assert Direction.from_value(-0.3) is Direction.NEGATIVE
    assert Direction.from_value(0.0) is Direction.POSITIVE
    with pytest.raises(ValueError):
        Direction.from_str("up")


def test_claim_tuple_roundtrip_and_schema():
    c = ClaimTuple("Flow Duration", Direction.POSITIVE, rank=1, magnitude=0.42)
    d = c.to_dict()
    jsonschema.validate(d, CLAIM_TUPLE_SCHEMA)
    assert ClaimTuple.from_dict(d) == c


def test_claim_tuple_validation():
    with pytest.raises(ValueError):
        ClaimTuple("", Direction.POSITIVE)
    with pytest.raises(ValueError):
        ClaimTuple("f", Direction.POSITIVE, rank=0)
    with pytest.raises(ValueError):
        ClaimTuple("f", Direction.POSITIVE, magnitude=float("nan"))


def test_claim_set_roundtrip_and_schema():
    cs = ClaimSet(
        instance_id="i0",
        claims=(
            ClaimTuple("f1", Direction.POSITIVE, 1, 0.5),
            ClaimTuple("f2", Direction.NEGATIVE, 2, None),
        ),
        extractor_id="eval_extractor",
        extractor_version="1.0.0",
        prompt_sha256="a" * 64,
    )
    d = cs.to_dict()
    jsonschema.validate(d, CLAIM_SET_SCHEMA)
    assert ClaimSet.from_dict(d) == cs


def test_explanation_record_roundtrip_and_schema():
    r = ExplanationRecord(
        instance_id="i0",
        generator_id="b1_template",
        text="Flow Duration increased the attack score.",
        llm_call_ids=("call-1",),
        abstained=False,
    )
    d = r.to_dict()
    jsonschema.validate(d, EXPLANATION_RECORD_SCHEMA)
    assert ExplanationRecord.from_dict(d) == r


def test_attribution_artifact_ranking_and_schema():
    a = AttributionArtifact(
        instance_id="i0",
        feature_names=("f1", "f2", "f3"),
        values=(0.1, -0.9, 0.3),
        base_value=0.5,
        method="treeshap",
        exact=True,
        background_policy="interventional_marginal",
    )
    jsonschema.validate(a.to_dict(), ATTRIBUTION_ARTIFACT_SCHEMA)
    assert a.ranked_features() == ("f2", "f3", "f1")
    assert a.ranked_features(top_k=2) == ("f2", "f3")
    assert a.sign_of("f2") is Direction.NEGATIVE
    assert AttributionArtifact.from_dict(a.to_dict()) == a


def test_attribution_length_mismatch_rejected():
    with pytest.raises(ValueError):
        AttributionArtifact(
            instance_id="i0",
            feature_names=("f1", "f2"),
            values=(0.1,),
            base_value=0.0,
            method="treeshap",
            exact=True,
            background_policy="x",
        )
