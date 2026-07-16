"""B5 — narrative Verify-then-Explain generator (L3).

Where B4 states per-feature facts, B5 weaves the SAME ranked evidence into ONE
coherent account of the prediction, grounded in the knowledge base twice over:
per-feature semantics (as B4) plus the PREDICTED CLASS's profile from
``kb/attack_classes`` — so the narrative "glue" (why this evidence means this
class) paraphrases a citable KB snippet instead of the LLM's prior. The
verification loop is deliberately the SAME instrument as B4 (draft → verify
claims against the SHAP evidence → on unsupported, abstain and degrade to B1):
the only delta between B4 and B5 is narrative synthesis, so the pair directly
measures whether coherence costs faithfulness (ε_nar).

B5 never had binary cached runs, so its single prompt is class-aware from
birth via ``{{score_label}}`` — no ``prompt_multiclass`` variant needed. On a
binary run the class profile for 'attack'/'benign' is absent from the KB and a
neutral placeholder is rendered.
"""

from __future__ import annotations

from typing import Any, Mapping

from faithfulids.framework import ExplanationRecord, GenerationContext, Generator
from faithfulids.generation.b1_template import B1Template
from faithfulids.generation.b4_vte.abstention import decide_abstention
from faithfulids.generation.b4_vte.generator import _default_verifier_model
from faithfulids.generation.b4_vte.kb_retrieval import KBRetriever
from faithfulids.generation.b4_vte.verifier.verifier import Verifier
from faithfulids.generation.base import ranked_feature_list, ranked_topk
from faithfulids.llm import load_prompt

#: Rendered when the predicted class has no KB profile (e.g. the binary
#: 'attack'/'benign' labels) — the narrative then rests on feature semantics only.
NO_CLASS_PROFILE = "(no class profile in the knowledge base)"


class B5NarrativeVtE(Generator):
    generator_id = "b5_narrative_vte"
    llm_dependent = True

    def __init__(
        self,
        config: dict,
        llm_client,
        model_config: dict,
        verifier: Verifier,
        kb: KBRetriever,
        class_kb: Mapping[str, str],
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
        self.class_kb = dict(class_kb)
        self.fallback = fallback

    def generate(self, context: GenerationContext) -> ExplanationRecord:
        rows = ranked_topk(context.attribution, self.top_k)
        rfl = ranked_feature_list(rows, context.score_label)
        kb_snippets = self.kb.snippets([r.feature for r in rows])
        class_snippet = self.class_kb.get(context.predicted_class) or NO_CLASS_PROFILE
        prompt = (
            self.template.replace("{{predicted_class}}", context.predicted_class)
            .replace("{{score_label}}", context.score_label)
            .replace("{{kb_class_snippet}}", class_snippet)
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
    kb_class_semantics: Mapping[str, str] | None = None,
    **_: object,
) -> B5NarrativeVtE:
    # Same injection contract as B4: the pilot injects the RuleVerifier so only
    # one LLM is loaded; the confirmatory path constructs the LLM Verifier.
    if verifier is None:
        vcfg = config["verifier"]
        verifier = Verifier(
            vcfg, llm_client, verifier_model_config or _default_verifier_model(vcfg)
        )
    kb = KBRetriever(kb_feature_semantics or {})
    fallback = B1Template(config["params"]["top_k"])
    return B5NarrativeVtE(
        config, llm_client, model_config, verifier, kb, kb_class_semantics or {}, fallback
    )
