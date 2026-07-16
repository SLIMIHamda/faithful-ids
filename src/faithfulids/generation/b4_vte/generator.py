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
from faithfulids.generation.base import (
    load_prompt_pair,
    ranked_feature_list,
    ranked_topk,
    select_template,
)


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
        self.template, self.template_multiclass = load_prompt_pair(config)
        self.client = llm_client
        self.model = model_config
        self.verifier = verifier
        self.kb = kb
        self.fallback = fallback

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        # The evidence list carries the score label, so the verifier checks the
        # draft against the SAME wording the drafter saw (its evidence regex keys
        # on the increases/decreases verbs, not the label).
        rfl = ranked_feature_list(rows, context.score_label)
        kb_snippets = self.kb.snippets([r.feature for r in rows])
        template = select_template(self.template, self.template_multiclass, context.score_label)
        prompt = (
            template.replace("{{predicted_class}}", context.predicted_class)
            .replace("{{ranked_feature_list}}", rfl)
            .replace("{{kb_feature_snippets}}", kb_snippets)
        )
        seed = int(context.metadata.get("seed", 0))
        draft = self.client.complete(
            model_config=self.model, prompt=prompt,
            params={"temperature": self.temperature, "top_k": self.top_k, "seed": seed},
        )
        verdict = self.verifier.verify(draft.text, rfl, seed=seed)
        call_ids = (draft.request_hash, verdict.call_id)
        # Verifier trace: WHY the draft was (dis)approved — the coverage/abstention
        # audit record (metadata was previously empty, hiding the abstention cause).
        trace = verdict.as_trace(getattr(self.verifier, "model_family", "unknown"))

        if decide_abstention(verdict.supported):
            fb = self.fallback.generate(context)
            return ExplanationRecord(
                instance_id=context.instance_id,
                generator_id=self.generator_id,
                text=fb.text,
                llm_call_ids=call_ids,
                abstained=True,
                fallback_generator_id=self.fallback.generator_id,
                metadata={"verifier_trace": trace},
            )
        return ExplanationRecord(
            instance_id=context.instance_id,
            generator_id=self.generator_id,
            text=draft.text,
            llm_call_ids=call_ids,
            abstained=False,
            metadata={"verifier_trace": trace},
        )


def build(
    config: dict,
    *,
    llm_client,
    model_config: dict,
    verifier=None,
    verifier_model_config: dict | None = None,
    kb_feature_semantics: Mapping[str, str] | None = None,
    **_: object,
) -> B4VtE:
    # A verifier may be INJECTED (e.g. the pilot's RuleVerifier, to avoid loading
    # a second model); otherwise construct the confirmatory LLM Verifier.
    if verifier is None:
        vcfg = config["verifier"]
        verifier = Verifier(
            vcfg, llm_client, verifier_model_config or _default_verifier_model(vcfg)
        )
    kb = KBRetriever(kb_feature_semantics or {})
    fallback = B1Template(config["params"]["top_k"])
    return B4VtE(config, llm_client, model_config, verifier, kb, fallback)
