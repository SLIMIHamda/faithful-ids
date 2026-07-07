"""Abstract interfaces for the pipeline's replaceable parts (L0).

These interfaces are the load-bearing *contracts* that make the extension story
(blueprint §7) real: a new generator, detector, attribution method, or metric is
added by implementing an interface + writing configs, with **zero** edits to
evaluation code.

The most important design decision in this module is a *type-level* one:

    A metric callable's signature **cannot** receive generator identity.

``Layer1Metric``, ``Layer2Metric`` and ``Layer2ModelMetric`` accept claims /
attributions / detector outputs only. Note the distinction the design turns on: a
metric MAY receive claim *content* (ε_nar and ε_model both need it), but NONE may
receive generator *identity*. "Which generator wrote this explanation" exists
solely as an opaque grouping key attached *downstream* by orchestration. This
converts "metrics never depend on a specific generation method" from a review-time
hope into a compile-time property (import-linter edge 1 forbids the import; these
signatures forbid the data path).

Pure L0: ``typing`` / ``abc`` only, no third-party or internal imports.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from faithfulids.framework.schemas import (
    AttributionArtifact,
    ClaimSet,
    ExplanationRecord,
)


# --------------------------------------------------------------------------- #
# L2 — detectors & attribution (interfaces defined here; implemented in L2)
# --------------------------------------------------------------------------- #
@runtime_checkable
class DetectorArtifact(Protocol):
    """A *frozen* trained detector, loaded for inference only.

    Inference code obtains one of these from ``models/`` and can never trigger
    training (import-linter edge 6). ``predict_proba`` returns the attack-class
    probability per row. A detector MAY additionally expose an optional
    ``predict_margin(rows)`` returning the raw log-odds / margin, consumed by
    margin-space Layer-2 deltas (which avoid probability saturation); it is not
    part of this required contract.
    """

    @property
    def feature_names(self) -> tuple[str, ...]: ...

    def predict_proba(self, rows: Sequence[Mapping[str, float]]) -> Sequence[float]: ...


class AttributionMethod(abc.ABC):
    """Base for TreeSHAP (exact) / DeepSHAP (approximate) wrappers."""

    #: Whether attributions are exact (True) or approximate (False). Consumed by
    #: the ε_att bookkeeping; declared in ``configs/attribution/*``.
    exact: bool

    @abc.abstractmethod
    def attribute(
        self,
        detector: DetectorArtifact,
        instances: Sequence[Mapping[str, float]],
        instance_ids: Sequence[str],
    ) -> list[AttributionArtifact]:
        """Attribute each instance against the frozen detector."""


# --------------------------------------------------------------------------- #
# L3 — generation & extraction
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GenerationContext:
    """Everything a generator is allowed to see for one instance.

    A generator receives the instance's features, the ground-truth attribution,
    the detector's prediction, and references (by id) to the KB and prompt it may
    use — but never the evaluation machinery or the reference against which it
    will be scored (import-linter edge 3).
    """

    instance_id: str
    feature_values: Mapping[str, float]
    attribution: AttributionArtifact
    detector_prediction: float
    predicted_class: str
    dataset_id: str
    kb_version: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class Generator(abc.ABC):
    """Base for the B0–B4 explanation generators.

    Adding B5 is a new subclass + config + prompt tree. Generators may not import
    ``metrics`` (edge 3). ``llm_dependent`` drives cell expansion: B0/B1 declare
    ``False`` (2 + 3×3 = 11 cells per dataset×detector).
    """

    #: Stable, opaque generator id (e.g. "b1_template"). Used only as a grouping
    #: key downstream — never passed to a metric.
    generator_id: str

    #: Whether the generator issues LLM calls. Read from the generator config.
    llm_dependent: bool

    @abc.abstractmethod
    def generate(self, context: GenerationContext) -> ExplanationRecord:
        """Produce one explanation record for the given context."""


class ClaimExtractor(abc.ABC):
    """Firewall side B — the evaluation claim extractor.

    Disjoint package / prompt / model family from the VtE verifier (edge 2). Its
    validity is established by gate EXP-G-001; orchestration refuses Layer-1
    metrics for any run not referencing a passing extractor-audit run id.
    """

    extractor_id: str
    extractor_version: str
    prompt_sha256: str

    @abc.abstractmethod
    def extract(self, explanation: ExplanationRecord) -> ClaimSet:
        """Extract structured claim tuples from an explanation's text."""


# --------------------------------------------------------------------------- #
# L4 — metrics. Note the ABSENCE of any generator-identity parameter.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetricSpec:
    """Identity + formula version of a metric (hostile-audit A12).

    A metric is admissible only after passing the RQ0 corruption battery; the
    ``formula_version`` here matches the version pinned in ``configs/metrics/*``.
    """

    name: str
    layer: str  # "layer1" | "layer2" | "meta" | "plausibility" | "cost"
    formula_version: str


@dataclass(frozen=True)
class MetricResult:
    """A single metric value for one instance, plus the spec that produced it.

    ``grouping`` is attached by orchestration *after* computation (generator id,
    llm id, dataset, detector, cell id). The metric callable itself never sees
    ``grouping`` — it is populated on the way out, not on the way in.
    """

    spec: MetricSpec
    instance_id: str
    value: float
    grouping: Mapping[str, str] = field(default_factory=dict)


@runtime_checkable
class Layer1Metric(Protocol):
    """Claim-level metric: mention P/R/F1, DSA, ARC, HFR.

    Receives the extracted claims and the reference attribution only. **No
    generator identity.**
    """

    spec: MetricSpec

    def __call__(
        self,
        claims: ClaimSet,
        attribution: AttributionArtifact,
        *,
        top_k: int | None = None,
    ) -> float: ...


@runtime_checkable
class ErasureOperator(Protocol):
    """Removes/replaces a set of features under a removal semantics.

    Primary = conditional-expectation imputation (per-class kNN / light
    generative model — a *fitted*, manifested cache artifact); secondary =
    retrain-based ROAR (anchor only). The erasure background is deliberately NOT
    the SHAP baseline distribution.
    """

    def erase(
        self,
        instance: Mapping[str, float],
        features_to_remove: Sequence[str],
    ) -> Mapping[str, float]: ...


@runtime_checkable
class Layer2Metric(Protocol):
    """ε_att erasure metric: comprehensiveness / sufficiency of the ATTRIBUTION's
    top-k features, at k ∈ {1,3,5}.

    Receives the attribution, the frozen detector, the instance, an erasure
    operator, and k — **no generator identity and no claims**. Being claim-free
    makes it generator-independent: it probes whether the attribution φ picks the
    features the model actually uses (φ ↔ f), i.e. the ε_att term. ``delta_space``
    selects probability (default) or margin/log-odds deltas.
    """

    spec: MetricSpec

    def __call__(
        self,
        attribution: AttributionArtifact,
        detector: DetectorArtifact,
        instance: Mapping[str, float],
        erasure: ErasureOperator,
        *,
        k: int,
        delta_space: str = "prob",
    ) -> float: ...


@runtime_checkable
class Layer2ModelMetric(Protocol):
    """ε_model erasure metric: comprehensiveness / sufficiency of the CITED
    features (S from the claim set), at k ∈ {1,3,5}.

    Receives the extracted ``ClaimSet`` — a legal metric input — the detector, the
    instance, an erasure operator, and k. It is claim-*aware* but still **never
    receives generator identity**: which generator authored the claims is attached
    downstream as an opaque grouping key, exactly as for Layer-1. It measures the
    gap between an explanation's claims and the model's true behaviour (claims ↔ f,
    the ε_model term of :mod:`faithfulids.framework.decomposition`), directly and
    without routing through the attribution. ``delta_space`` selects probability
    (default) or margin/log-odds deltas.
    """

    spec: MetricSpec

    def __call__(
        self,
        claims: ClaimSet,
        detector: DetectorArtifact,
        instance: Mapping[str, float],
        erasure: ErasureOperator,
        *,
        k: int,
        delta_space: str = "prob",
    ) -> float: ...
