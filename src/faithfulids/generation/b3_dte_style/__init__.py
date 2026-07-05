"""B3 — Decision-Tree-Explanation-style generation (L3).

Shows the model the ranked attribution and asks it to narrate the decision path.
Wires the frozen DTE-style prompt (by hash) through the LLM client.
"""

from __future__ import annotations

from faithfulids.framework import ExplanationRecord, GenerationContext, Generator
from faithfulids.generation.base import ranked_feature_list, ranked_topk
from faithfulids.llm import load_prompt


class B3DteStyle(Generator):
    generator_id = "b3_dte_style"
    llm_dependent = True

    def __init__(self, config: dict, llm_client, model_config: dict) -> None:
        self.top_k = config["params"]["top_k"]
        self.temperature = config["params"]["temperature"]
        p = config["prompt"]
        self.template = load_prompt(p["name"], p["version"], expected_sha256=p["sha256"])
        self.client = llm_client
        self.model = model_config

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        prompt = self.template.replace(
            "{{predicted_class}}", context.predicted_class
        ).replace("{{ranked_feature_list}}", ranked_feature_list(rows))
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


def build(config: dict, *, llm_client, model_config: dict, **_: object) -> B3DteStyle:
    return B3DteStyle(config, llm_client, model_config)
