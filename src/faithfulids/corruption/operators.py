"""RQ0 corruption operators (L3).

Inject KNOWN errors into faithful-by-construction claim sets (B1's claims),
emitting per-instance ground-truth labels. These labels are the reference
against which RQ0 meta-validation (metrics/meta) measures each metric's
sensitivity/specificity — the mechanism that makes "metrics are validated, not
assumed" a registered gate (EXP-G-002).

Operators consume a :class:`ClaimSet` (framework type) — they never import
``generation`` (independent L3 sibling). Each operator is deterministic and pure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from faithfulids.framework import ClaimSet, ClaimTuple, Direction


@dataclass(frozen=True)
class CorruptionResult:
    operator: str
    label: str  # always "corrupted" — the ground-truth for RQ0
    claims: ClaimSet
    detail: str


def _highest_magnitude_index(claims: tuple[ClaimTuple, ...]) -> int:
    return max(
        range(len(claims)),
        key=lambda i: (claims[i].magnitude if claims[i].magnitude is not None else 0.0),
    )


def _rank_one_index(claims: tuple[ClaimTuple, ...]) -> int:
    for i, c in enumerate(claims):
        if c.rank == 1:
            return i
    return 0


def _replace(cs: ClaimSet, claims: tuple[ClaimTuple, ...]) -> ClaimSet:
    return ClaimSet(
        instance_id=cs.instance_id, claims=claims, extractor_id=cs.extractor_id,
        extractor_version=cs.extractor_version, prompt_sha256=cs.prompt_sha256,
    )


def fabricated_feature(cs: ClaimSet, params: Mapping[str, Any]) -> CorruptionResult:
    absent = params.get("absent_feature", "FABRICATED_FEATURE")
    new_rank = 1 + max((c.rank or 0) for c in cs.claims) if cs.claims else 1
    added = ClaimTuple(feature=absent, direction=Direction.POSITIVE, rank=new_rank, magnitude=0.5)
    return CorruptionResult("fabricated_feature", "corrupted", _replace(cs, cs.claims + (added,)),
                            f"added claim for absent feature {absent!r}")


def sign_flip(cs: ClaimSet, params: Mapping[str, Any]) -> CorruptionResult:
    claims = list(cs.claims)
    i = _highest_magnitude_index(cs.claims)
    c = claims[i]
    flipped = Direction.NEGATIVE if c.direction is Direction.POSITIVE else Direction.POSITIVE
    claims[i] = ClaimTuple(c.feature, flipped, c.rank, c.magnitude)
    return CorruptionResult("sign_flip", "corrupted", _replace(cs, tuple(claims)),
                            f"flipped direction of {c.feature!r}")


def rank_inversion(cs: ClaimSet, params: Mapping[str, Any]) -> CorruptionResult:
    claims = list(cs.claims)
    if len(claims) >= 2:
        a, b = claims[0], claims[1]
        claims[0] = ClaimTuple(a.feature, a.direction, b.rank, a.magnitude)
        claims[1] = ClaimTuple(b.feature, b.direction, a.rank, b.magnitude)
    return CorruptionResult("rank_inversion", "corrupted", _replace(cs, tuple(claims)),
                            "swapped ranks of the top two claims")


def omission(cs: ClaimSet, params: Mapping[str, Any]) -> CorruptionResult:
    i = _rank_one_index(cs.claims)
    claims = tuple(c for j, c in enumerate(cs.claims) if j != i)
    return CorruptionResult("omission", "corrupted", _replace(cs, claims),
                            "omitted the rank-1 claim")


def magnitude_inflation(cs: ClaimSet, params: Mapping[str, Any]) -> CorruptionResult:
    factor = float(params.get("factor", 3.0))
    claims = list(cs.claims)
    i = _highest_magnitude_index(cs.claims)
    c = claims[i]
    mag = (c.magnitude if c.magnitude is not None else 1.0) * factor
    claims[i] = ClaimTuple(c.feature, c.direction, c.rank, mag)
    return CorruptionResult("magnitude_inflation", "corrupted", _replace(cs, tuple(claims)),
                            f"inflated magnitude of {c.feature!r} by {factor}x")


def vague_substitution(cs: ClaimSet, params: Mapping[str, Any]) -> CorruptionResult:
    vague = params.get("replace_with", "an unspecified traffic feature")
    claims = list(cs.claims)
    i = _rank_one_index(cs.claims)
    c = claims[i]
    claims[i] = ClaimTuple(vague, c.direction, c.rank, c.magnitude)
    return CorruptionResult("vague_substitution", "corrupted", _replace(cs, tuple(claims)),
                            f"replaced {c.feature!r} with a vague phrase")


OPERATORS: dict[str, Callable[[ClaimSet, Mapping[str, Any]], CorruptionResult]] = {
    "fabricated_feature": fabricated_feature,
    "sign_flip": sign_flip,
    "rank_inversion": rank_inversion,
    "omission": omission,
    "magnitude_inflation": magnitude_inflation,
    "vague_substitution": vague_substitution,
}


def apply_operator(name: str, cs: ClaimSet, params: Mapping[str, Any] | None = None) -> CorruptionResult:
    if name not in OPERATORS:
        raise KeyError(f"unknown corruption operator: {name!r}")
    return OPERATORS[name](cs, params or {})
