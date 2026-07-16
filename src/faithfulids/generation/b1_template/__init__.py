"""B1 — deterministic template (L3). LLM-independent, faithful by construction.

B1 renders the top-k attribution into a fixed, human-readable template whose
claims exactly match the attribution (direction = sign, rank = |value| order).
Its narration error ε_nar ≈ 0 by design. B1 is therefore:

* the reference "faithful" generator in the plausibility–faithfulness gap;
* the base over which the RQ0 corruption operators inject known errors;
* the fallback target for B4 abstention (never silence).
"""

from __future__ import annotations

from faithfulids.framework import (
    ClaimTuple,
    ExplanationRecord,
    GenerationContext,
    Generator,
)
from faithfulids.generation.base import ranked_topk


class B1Template(Generator):
    generator_id = "b1_template"
    llm_dependent = False

    def __init__(self, top_k: int) -> None:
        self.top_k = top_k

    def faithful_claims(self, context: GenerationContext) -> tuple[ClaimTuple, ...]:
        """The exact claim tuples B1 asserts (faithful by construction)."""
        rows = ranked_topk(context.attribution, self.top_k)
        return tuple(
            ClaimTuple(
                feature=r.feature, direction=r.direction, rank=r.rank,
                magnitude=abs(r.value),
            )
            for r in rows
        )

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        parts = []
        for r in rows:
            word = "increased" if r.direction.sign > 0 else "decreased"
            # score_label: binary renders the frozen literal "attack" (byte-identical
            # to every cached run); multi-class renders the predicted class, so the
            # sentence stays TRUE on BENIGN-predicted instances — B1 is the
            # faithful-by-construction reference and must never assert a false
            # direction.
            parts.append(
                f"{r.rank}. {r.feature} {word} the {context.score_label} score "
                f"(magnitude {abs(r.value):.4f})"
            )
        text = (
            f"The model classified this flow as {context.predicted_class}. "
            f"The most influential factors were: " + "; ".join(parts) + "."
        )
        return ExplanationRecord(
            instance_id=context.instance_id,
            generator_id=self.generator_id,
            text=text,
        )


def build(config: dict, **_: object) -> B1Template:
    return B1Template(config["params"]["top_k"])
