"""framework — L0, the formal spine (pure; no I/O, no deps, no internal imports).

Claim/explanation/attribution schemas, the replaceable-part interfaces, and the
ε_model ≲ ε_nar + ε_att decomposition. This is the only ``src`` module that both
``metrics`` and ``analysis`` are permitted to import for its type definitions.
"""

from __future__ import annotations

from faithfulids.framework.decomposition import (
    ErrorComponent,
    FaithfulnessDecomposition,
)
from faithfulids.framework.interfaces import (
    AttributionMethod,
    ClaimExtractor,
    DetectorArtifact,
    ErasureOperator,
    GenerationContext,
    Generator,
    Layer1Metric,
    Layer2Metric,
    MetricResult,
    MetricSpec,
)
from faithfulids.framework.schemas import (
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

__all__ = [
    # schemas
    "Direction",
    "ClaimTuple",
    "ClaimSet",
    "ExplanationRecord",
    "AttributionArtifact",
    "CLAIM_TUPLE_SCHEMA",
    "CLAIM_SET_SCHEMA",
    "EXPLANATION_RECORD_SCHEMA",
    "ATTRIBUTION_ARTIFACT_SCHEMA",
    # interfaces
    "DetectorArtifact",
    "AttributionMethod",
    "GenerationContext",
    "Generator",
    "ClaimExtractor",
    "ErasureOperator",
    "Layer1Metric",
    "Layer2Metric",
    "MetricSpec",
    "MetricResult",
    # decomposition
    "ErrorComponent",
    "FaithfulnessDecomposition",
]
