"""B0 — raw SHAP dump (L3). LLM-independent, deterministic.

The baseline "explanation" that is just the attribution vector rendered as text.
Faithful trivially (it *is* the attribution) but not an explanation a human would
read — the floor of the generator axis.
"""

from __future__ import annotations

from faithfulids.framework import ExplanationRecord, GenerationContext, Generator
from faithfulids.generation.base import ranked_topk


class B0RawShap(Generator):
    generator_id = "b0_raw_shap"
    llm_dependent = False

    def __init__(self, top_k: int) -> None:
        self.top_k = top_k

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        body = "; ".join(f"{r.feature}={r.value:+.4f}" for r in rows)
        text = f"SHAP attribution (top-{self.top_k}) for class {context.predicted_class}: {body}"
        return ExplanationRecord(
            instance_id=context.instance_id,
            generator_id=self.generator_id,
            text=text,
        )


def build(config: dict, **_: object) -> B0RawShap:
    return B0RawShap(config["params"]["top_k"])
