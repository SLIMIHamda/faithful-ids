"""B1ℓ — LLM-rendered top-k SHAP (L3), a CEILING generator.

This is B1 (render top-k SHAP into fixed prose) with an LLM as the renderer
instead of a fixed template: the model is shown the ranked attribution and asked
to recite it. It carries the prompt that formerly served as b3's K-way variant
(``b3_dte_style`` 1.1.0), whose "proceed down the list, reference only the
factors provided" wording pins precision/recall/rank/direction at ceiling by
construction — so its scores measure the extractor, not the model, and it is
treated like B0/B1: a ceiling, anchor-LLM only, excluded from the confirmatory
generator ranking (prereg amendment 0002).

It renders exactly the same evidence B1 does — the ranked SHAP list — and NO
knowledge-base snippets: it is not grounded generation, it is transcription.
That is the whole point of keeping it: it proves the extractor is not the
bottleneck at the anchor LLM, so any B4/B5 shortfall cannot be attributed to
measurement.
"""

from __future__ import annotations

from faithfulids.framework import ExplanationRecord, GenerationContext, Generator
from faithfulids.generation.base import (
    load_prompt_pair,
    ranked_feature_list,
    ranked_topk,
    select_template,
)


class B1LlmRender(Generator):
    generator_id = "b1l_llm_render"
    llm_dependent = True

    def __init__(self, config: dict, llm_client, model_config: dict) -> None:
        self.top_k = config["params"]["top_k"]
        self.temperature = config["params"]["temperature"]
        self.template, self.template_multiclass = load_prompt_pair(config)
        self.client = llm_client
        self.model = model_config

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        template = select_template(self.template, self.template_multiclass, context.score_label)
        prompt = template.replace(
            "{{predicted_class}}", context.predicted_class
        ).replace("{{ranked_feature_list}}", ranked_feature_list(rows, context.score_label))
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


def build(config: dict, *, llm_client, model_config: dict, **_: object) -> B1LlmRender:
    return B1LlmRender(config, llm_client, model_config)
