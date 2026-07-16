"""B2 — zero-shot LLM generation (L3). The conference method.

Wires the frozen zero-shot prompt (by hash) through the ledger-backed LLM
client. The generator never sees how it will be scored (edge 3).
"""

from __future__ import annotations

from faithfulids.framework import ExplanationRecord, GenerationContext, Generator
from faithfulids.generation.base import feature_value_table, load_prompt_pair, select_template


class B2ZeroShot(Generator):
    generator_id = "b2_zeroshot"
    llm_dependent = True

    def __init__(self, config: dict, llm_client, model_config: dict) -> None:
        self.top_k = config["params"]["top_k"]
        self.temperature = config["params"]["temperature"]
        self.template, self.template_multiclass = load_prompt_pair(config)
        self.client = llm_client
        self.model = model_config

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        template = select_template(self.template, self.template_multiclass, context.score_label)
        prompt = template.replace(
            "{{predicted_class}}", context.predicted_class
        ).replace("{{feature_table}}", feature_value_table(dict(context.feature_values)))
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


def build(config: dict, *, llm_client, model_config: dict, **_: object) -> B2ZeroShot:
    return B2ZeroShot(config, llm_client, model_config)
