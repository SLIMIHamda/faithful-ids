"""B3 — grounded-natural generation (L3), the "grounding without enforcement" baseline.

Shows the model the ranked attribution AND the feature-semantics KB snippets and
asks it to explain the decision in its own words. Under the K-way task this is
b4_vte's drafting prompt with verification disabled (b3 prompt 1.2.0): identical
evidence, no verifier — so the B3↔B4 delta isolates verification (prereg
amendment 0002). The binary path keeps the frozen v1.0.0 prompt (its wording is
baked into every cached run's request hashes) and carries no KB snippets (the
binary template has no ``{{kb_feature_snippets}}`` placeholder, so the KB
substitution below is a no-op there — replay-safe).

The transcription-style prompt B3 used before (1.1.0) now lives as the
``b1l_llm_render`` ceiling generator.
"""

from __future__ import annotations

from typing import Mapping

from faithfulids.framework import ExplanationRecord, GenerationContext, Generator
from faithfulids.generation.b4_vte.kb_retrieval import KBRetriever  # shared KB grounding (as b5 does)
from faithfulids.generation.base import (
    load_prompt_pair,
    ranked_feature_list,
    ranked_topk,
    select_template,
)


class B3DteStyle(Generator):
    generator_id = "b3_dte_style"
    llm_dependent = True

    def __init__(self, config: dict, llm_client, model_config: dict, kb: KBRetriever) -> None:
        self.top_k = config["params"]["top_k"]
        self.temperature = config["params"]["temperature"]
        self.template, self.template_multiclass = load_prompt_pair(config)
        self.client = llm_client
        self.model = model_config
        self.kb = kb

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        template = select_template(self.template, self.template_multiclass, context.score_label)
        # Same evidence B4 drafts from: the ranked list AND the KB snippets for the
        # SAME top-k features. If B3 saw less than B4, evidence would be confounded
        # with enforcement. On the binary v1.0.0 template the kb placeholder is
        # absent, so this replace is a no-op (cached-run hash continuity).
        prompt = (
            template.replace("{{predicted_class}}", context.predicted_class)
            .replace("{{ranked_feature_list}}", ranked_feature_list(rows, context.score_label))
            .replace("{{kb_feature_snippets}}", self.kb.snippets([r.feature for r in rows]))
        )
        params = {
            "temperature": self.temperature,
            "top_k": self.top_k,
            "seed": int(context.metadata.get("seed", 0)),
        }
        resp = self.client.complete(model_config=self.model, prompt=prompt, params=params)
        return ExplanationRecord(
            instance_id=context.instance_id,
            generator_id=self.generator_id,
            text=resp.text,
            llm_call_ids=(resp.request_hash,),
        )


def build(
    config: dict,
    *,
    llm_client,
    model_config: dict,
    kb_feature_semantics: Mapping[str, str] | None = None,
    **_: object,
) -> B3DteStyle:
    return B3DteStyle(config, llm_client, model_config, KBRetriever(kb_feature_semantics or {}))
