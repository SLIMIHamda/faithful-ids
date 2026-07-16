"""Formal schemas — the paper's §3 in code (L0).

This module defines the *shapes* the whole pipeline agrees on:

* :class:`ClaimTuple` — the atomic unit of a faithfulness claim
  ``(feature, direction, rank, magnitude)`` extracted from an explanation;
* :class:`ClaimSet` — the extractor's output for one instance, stamped with the
  extractor identity and prompt hash (firewall side B provenance);
* :class:`ExplanationRecord` — one generated explanation with its opaque
  generator id, LLM-call ids, and abstention flag;
* :class:`AttributionArtifact` — a SHAP (or other) attribution vector for one
  instance, tagged exact-vs-approximate for the ε_att bookkeeping.

**Purity.** ``framework`` is L0: it imports nothing internal and depends on no
third-party package (import-linter edge 7). JSON Schemas are provided as plain
``dict`` constants so callers may validate with ``jsonschema`` *outside* this
layer without this layer taking the dependency.

There are **no scientific parameters here** — only structure. Feature names,
thresholds, k values, seeds, and model names all arrive from ``configs/``.
"""

from __future__ import annotations

import enum
import math
from dataclasses import asdict, dataclass, field
from typing import Any


class Direction(enum.Enum):
    """Sign of a feature's claimed contribution to the attack score.

    ``POSITIVE`` = the feature is claimed to push the prediction *towards*
    "attack"; ``NEGATIVE`` = *away*. The canonical serialisation is ``"+"`` /
    ``"-"`` so that a claim tuple round-trips through JSON unambiguously.
    """

    POSITIVE = "+"
    NEGATIVE = "-"

    @property
    def sign(self) -> int:
        return 1 if self is Direction.POSITIVE else -1

    @classmethod
    def from_str(cls, value: str) -> "Direction":
        try:
            return cls(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"invalid direction {value!r}; expected one of {[d.value for d in cls]}"
            ) from exc

    @classmethod
    def from_value(cls, value: float) -> "Direction":
        """Direction implied by a signed attribution value (0 → POSITIVE)."""
        return cls.POSITIVE if value >= 0 else cls.NEGATIVE


@dataclass(frozen=True)
class ClaimTuple:
    """An atomic, extracted faithfulness claim.

    ``rank`` is 1-indexed (1 = most important feature the explanation names) or
    ``None`` if the explanation stated no ordering. ``magnitude`` is the claimed
    attribution magnitude or ``None`` if unquantified. Only ``feature`` and
    ``direction`` are mandatory — a bare "feature X increased the risk" claim is
    representable.

    ``direction_evidence`` records HOW the extractor obtained ``direction``
    (additive, 2026-07-11 audit follow-up): ``"word"`` (explicit direction cue),
    ``"number"`` (signed attribution value), ``"llm"`` (extractor model's JSON),
    or ``"default"`` (no textual evidence — the extractor's fallback sign).
    ``None`` means unrecorded (legacy claims, corruption-built claims) and is
    treated as asserted by the metrics: only an explicit ``"default"`` marks a
    guess. This keeps ``direction`` always populated (schema unchanged for
    consumers) while letting Layer-1 separate reading fidelity (``dsa_asserted``)
    from assertion style (``direction_assertion_rate``).
    """

    _EVIDENCE_VALUES = (None, "word", "number", "llm", "default")

    feature: str
    direction: Direction
    rank: int | None = None
    magnitude: float | None = None
    direction_evidence: str | None = None

    def __post_init__(self) -> None:
        if not self.feature:
            raise ValueError("ClaimTuple.feature must be a non-empty string")
        if self.rank is not None and self.rank < 1:
            raise ValueError("ClaimTuple.rank is 1-indexed and must be >= 1")
        if self.magnitude is not None and (
            math.isnan(self.magnitude) or math.isinf(self.magnitude)
        ):
            raise ValueError("ClaimTuple.magnitude must be finite")
        if self.direction_evidence not in self._EVIDENCE_VALUES:
            raise ValueError(
                f"ClaimTuple.direction_evidence must be one of {self._EVIDENCE_VALUES}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "direction": self.direction.value,
            "rank": self.rank,
            "magnitude": self.magnitude,
            "direction_evidence": self.direction_evidence,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ClaimTuple":
        return cls(
            feature=d["feature"],
            direction=Direction.from_str(d["direction"]),
            rank=d.get("rank"),
            magnitude=d.get("magnitude"),
            direction_evidence=d.get("direction_evidence"),
        )


@dataclass(frozen=True)
class ClaimSet:
    """The extractor's structured output for one explanation instance.

    Stamped with the extractor identity, version, and prompt sha256 so that
    every downstream Layer-1 number can be traced to the exact (firewalled)
    instrument that produced its claims (blueprint §6).
    """

    instance_id: str
    claims: tuple[ClaimTuple, ...]
    extractor_id: str
    extractor_version: str
    prompt_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "claims": [c.to_dict() for c in self.claims],
            "extractor_id": self.extractor_id,
            "extractor_version": self.extractor_version,
            "prompt_sha256": self.prompt_sha256,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ClaimSet":
        return cls(
            instance_id=d["instance_id"],
            claims=tuple(ClaimTuple.from_dict(c) for c in d["claims"]),
            extractor_id=d["extractor_id"],
            extractor_version=d["extractor_version"],
            prompt_sha256=d["prompt_sha256"],
        )


@dataclass(frozen=True)
class ExplanationRecord:
    """One generated explanation.

    ``generator_id`` is carried here as *provenance*, but it is deliberately an
    opaque string: metric functions never receive it (generator-blindness is a
    type-level property — see :mod:`faithfulids.framework.interfaces`).
    ``llm_call_ids`` point into the append-only LLM ledger, enabling L3 replay.
    ``abstained`` records a VtE abstention; ``fallback_generator_id`` records the
    generator the pipeline degraded to (never silence — blueprint §8 rule 3).
    """

    instance_id: str
    generator_id: str
    text: str
    llm_call_ids: tuple[str, ...] = ()
    abstained: bool = False
    fallback_generator_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "generator_id": self.generator_id,
            "text": self.text,
            "llm_call_ids": list(self.llm_call_ids),
            "abstained": self.abstained,
            "fallback_generator_id": self.fallback_generator_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ExplanationRecord":
        return cls(
            instance_id=d["instance_id"],
            generator_id=d["generator_id"],
            text=d["text"],
            llm_call_ids=tuple(d.get("llm_call_ids", ())),
            abstained=bool(d.get("abstained", False)),
            fallback_generator_id=d.get("fallback_generator_id"),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass(frozen=True)
class AttributionArtifact:
    """A per-instance attribution vector (SHAP or other).

    ``exact`` distinguishes exact TreeSHAP from approximate DeepSHAP; the ε_att
    bookkeeping (:mod:`faithfulids.framework.decomposition`) consumes this flag.
    ``background_policy`` records the removal semantics pinned in
    ``configs/attribution/*``. This is the ground-truth attribution against which
    Layer-1 claim faithfulness is measured — it is never the erasure background
    (blueprint: erasure background is deliberately NOT the SHAP baseline).

    ``explained_class`` (additive, queue #5.3b) records WHICH class this vector
    explains. Mandatory provenance under a multi-class detector: each instance's
    attribution is selected for the class the detector predicted, so without this
    field two exported vectors can be about different classes with nothing saying
    so, and the export is uninterpretable. ``None`` = unrecorded (legacy binary
    artifacts, whose vectors explain the positive/attack side).
    """

    instance_id: str
    feature_names: tuple[str, ...]
    values: tuple[float, ...]
    base_value: float
    method: str
    exact: bool
    background_policy: str
    explained_class: str | None = None

    def __post_init__(self) -> None:
        if len(self.feature_names) != len(self.values):
            raise ValueError(
                "AttributionArtifact.feature_names and values must be the same length"
            )

    def value_of(self, feature: str) -> float:
        return self.values[self.feature_names.index(feature)]

    def sign_of(self, feature: str) -> Direction:
        return Direction.from_value(self.value_of(feature))

    def ranked_features(self, top_k: int | None = None) -> tuple[str, ...]:
        """Features ordered by descending absolute attribution (rank 1 first)."""
        order = sorted(
            range(len(self.values)), key=lambda i: abs(self.values[i]), reverse=True
        )
        names = tuple(self.feature_names[i] for i in order)
        return names if top_k is None else names[:top_k]

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "feature_names": list(self.feature_names),
            "values": list(self.values),
            "base_value": self.base_value,
            "method": self.method,
            "exact": self.exact,
            "background_policy": self.background_policy,
            "explained_class": self.explained_class,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AttributionArtifact":
        return cls(
            instance_id=d["instance_id"],
            feature_names=tuple(d["feature_names"]),
            values=tuple(float(v) for v in d["values"]),
            base_value=float(d["base_value"]),
            method=d["method"],
            exact=bool(d["exact"]),
            background_policy=d["background_policy"],
            explained_class=d.get("explained_class"),
        )


def as_json_dict(obj: Any) -> dict[str, Any]:
    """Best-effort canonical dict for any framework dataclass instance."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()  # type: ignore[no-any-return]
    return asdict(obj)


# --------------------------------------------------------------------------- #
# JSON Schemas as plain-dict constants (no jsonschema import at L0). Callers in
# higher layers / tests validate instances against these.
# --------------------------------------------------------------------------- #
CLAIM_TUPLE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "faithfulids/framework/claim_tuple.v1.json",
    "type": "object",
    "additionalProperties": False,
    "required": ["feature", "direction"],
    "properties": {
        "feature": {"type": "string", "minLength": 1},
        "direction": {"enum": ["+", "-"]},
        "rank": {"type": ["integer", "null"], "minimum": 1},
        "magnitude": {"type": ["number", "null"]},
        # additive (2026-07-11): how the extractor obtained `direction`;
        # null = unrecorded (legacy / corruption-built claims).
        "direction_evidence": {"enum": [None, "word", "number", "llm", "default"]},
    },
}

CLAIM_SET_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "faithfulids/framework/claim_set.v1.json",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "instance_id",
        "claims",
        "extractor_id",
        "extractor_version",
        "prompt_sha256",
    ],
    "properties": {
        "instance_id": {"type": "string", "minLength": 1},
        "claims": {"type": "array", "items": CLAIM_TUPLE_SCHEMA},
        "extractor_id": {"type": "string", "minLength": 1},
        "extractor_version": {"type": "string", "minLength": 1},
        "prompt_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    },
}

EXPLANATION_RECORD_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "faithfulids/framework/explanation_record.v1.json",
    "type": "object",
    "additionalProperties": False,
    "required": ["instance_id", "generator_id", "text"],
    "properties": {
        "instance_id": {"type": "string", "minLength": 1},
        "generator_id": {"type": "string", "minLength": 1},
        "text": {"type": "string"},
        "llm_call_ids": {"type": "array", "items": {"type": "string"}},
        "abstained": {"type": "boolean"},
        "fallback_generator_id": {"type": ["string", "null"]},
        "metadata": {"type": "object"},
    },
}

ATTRIBUTION_ARTIFACT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "faithfulids/framework/attribution_artifact.v1.json",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "instance_id",
        "feature_names",
        "values",
        "base_value",
        "method",
        "exact",
        "background_policy",
    ],
    "properties": {
        "instance_id": {"type": "string", "minLength": 1},
        "feature_names": {"type": "array", "items": {"type": "string"}},
        "values": {"type": "array", "items": {"type": "number"}},
        "base_value": {"type": "number"},
        "method": {"type": "string", "minLength": 1},
        "exact": {"type": "boolean"},
        "background_policy": {"type": "string", "minLength": 1},
        # additive (queue #5.3b): which class this vector explains; null =
        # unrecorded (legacy binary artifacts explain the positive/attack side).
        "explained_class": {"type": ["string", "null"]},
    },
}
