"""RQ0 corruption operators: correct mutation + ground-truth labels."""

from __future__ import annotations

from faithfulids.corruption import OPERATORS, apply_operator
from faithfulids.framework import ClaimSet, ClaimTuple, Direction


def _faithful() -> ClaimSet:
    return ClaimSet(
        instance_id="i0",
        claims=(
            ClaimTuple("Flow Duration", Direction.POSITIVE, rank=1, magnitude=0.8),
            ClaimTuple("Flow Bytes/s", Direction.POSITIVE, rank=2, magnitude=0.5),
            ClaimTuple("SYN Flag Count", Direction.NEGATIVE, rank=3, magnitude=0.3),
        ),
        extractor_id="eval_extractor",
        extractor_version="1.0.0",
        prompt_sha256="a" * 64,
    )


def test_all_six_operators_present_and_label_corrupted():
    cs = _faithful()
    assert set(OPERATORS) == {
        "fabricated_feature", "sign_flip", "rank_inversion",
        "omission", "magnitude_inflation", "vague_substitution",
    }
    for name in OPERATORS:
        res = apply_operator(name, cs, {})
        assert res.label == "corrupted"
        assert res.operator == name


def test_fabricated_feature_adds_absent_claim():
    res = apply_operator("fabricated_feature", _faithful(), {"absent_feature": "Ghost"})
    features = [c.feature for c in res.claims.claims]
    assert "Ghost" in features
    assert len(features) == 4


def test_sign_flip_flips_highest_magnitude():
    res = apply_operator("sign_flip", _faithful(), {})
    fd = next(c for c in res.claims.claims if c.feature == "Flow Duration")
    assert fd.direction is Direction.NEGATIVE  # was POSITIVE, highest magnitude


def test_omission_drops_rank_one():
    res = apply_operator("omission", _faithful(), {})
    assert all(c.feature != "Flow Duration" for c in res.claims.claims)
    assert len(res.claims.claims) == 2


def test_magnitude_inflation_scales():
    res = apply_operator("magnitude_inflation", _faithful(), {"factor": 3.0})
    fd = next(c for c in res.claims.claims if c.feature == "Flow Duration")
    assert fd.magnitude == 0.8 * 3.0


def test_vague_substitution_replaces_rank_one_name():
    res = apply_operator("vague_substitution", _faithful(), {"replace_with": "some feature"})
    assert any(c.feature == "some feature" for c in res.claims.claims)


def test_rank_inversion_swaps_top_two_ranks():
    res = apply_operator("rank_inversion", _faithful(), {})
    by_feature = {c.feature: c.rank for c in res.claims.claims}
    assert by_feature["Flow Duration"] == 2
    assert by_feature["Flow Bytes/s"] == 1
