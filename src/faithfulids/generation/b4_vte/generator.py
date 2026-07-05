"""B4 — Verify-then-Explain generator (L3).

Draft (LLM) → verify (firewalled internal verifier) → on unsupported, abstain and
degrade to B1 (never silence). The verifier is side A of the circularity
firewall; B4 never imports the evaluation extractor or metrics.
"""

from __future__ import annotations

from typing import Any, Mapping

from faithfulids.framework import ExplanationRecord, GenerationContext, Generator
from faithfulids.generation.b1_template import B1Template
from faithfulids.generation.b4_vte.abstention import decide_abstention
from faithfulids.generation.b4_vte.kb_retrieval import KBRetriever
from faithfulids.generation.b4_vte.verifier.verifier import Verifier
from faithfulids.generation.base import ranked_feature_list, ranked_topk
from faithfulids.llm import load_prompt


def _default_verifier_model(verifier_config: Mapping[str, Any]) -> dict[str, Any]:
    """A minimal model config for the verifier from its declared family.

    The verifier family is firewall-disjoint from every generator LLM and the
    extractor; it has no entry in ``configs/llms`` by design, so its identity is
    synthesised here from the b4 verifier block (pinned revision required).
    """
    return {
        "id": "vte_verifier",
        "model_family": verifier_config["model_family"],
        "provider": "local_open_weights",
        "weights": {"hf_repo": "", "revision": "pin-pending", "sha256": None},
    }


class B4VtE(Generator):
    generator_id = "b4_vte"
    llm_dependent = True

    def __init__(
        self,
        config: dict,
        llm_client,
        model_config: dict,
        verifier: Verifier,
        kb: KBRetriever,
        fallback: B1Template,
    ) -> None:
        self.top_k = config["params"]["top_k"]
        self.temperature = config["params"]["temperature"]
        p = config["prompt"]
        self.template = load_prompt(p["name"], p["version"], expected_sha256=p["sha256"])
        self.client = llm_client
        self.model = model_config
        self.verifier = verifier
        self.kb = kb
        self.fallback = fallback

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        rfl = ranked_feature_list(rows)
        kb_snippets = self.kb.snippets([r.feature for r in rows])
        prompt = (
            self.template.replace("{{predicted_class}}", context.predicted_class)
            .replace("{{ranked_feature_list}}", rfl)
            .replace("{{kb_feature_snippets}}", kb_snippets)
        )
        seed = int(context.metadata.get("seed", 0))
        draft = self.client.complete(
            model_config=self.model, prompt=prompt,
            params={"temperature": self.temperature, "top_k": self.top_k, "seed": seed},
        )
        supported, verify_call = self.verifier.verify(draft.text, rfl, seed=seed)
        call_ids = (draft.request_hash, verify_call)

        if decide_abstention(supported):
            fb = self.fallback.generate(context)
            return ExplanationRecord(
                instance_id=context.instance_id,
                generator_id=self.generator_id,
                text=fb.text,
                llm_call_ids=call_ids,
                abstained=True,
                fallback_generator_id=self.fallback.generator_id,
            )
        return ExplanationRecord(
            instance_id=context.instance_id,
            generator_id=self.generator_id,
            text=draft.text,
            llm_call_ids=call_ids,
            abstained=False,
        )


def build(
    config: dict,
    *,
    llm_client,
    model_config: dict,
    verifier_model_config: dict | None = None,
    kb_feature_semantics: Mapping[str, str] | None = None,
    **_: object,
) -> B4VtE:
    vcfg = config["verifier"]
    verifier = Verifier(
        vcfg, llm_client, verifier_model_config or _default_verifier_model(vcfg)
    )
    kb = KBRetriever(kb_feature_semantics or {})
    fallback = B1Template(config["params"]["top_k"])
    return B4VtE(config, llm_client, model_config, verifier, kb, fallback)
