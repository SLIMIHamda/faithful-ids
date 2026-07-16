"""Generators: B0/B1 deterministic + faithful; B2 wired; B4 abstains to B1."""

from __future__ import annotations

from faithfulids.framework import AttributionArtifact, GenerationContext
from faithfulids.generation import get_generator
from faithfulids.llm import CallLedger, LLMClient
from faithfulids.llm.providers import DeterministicStubProvider
from faithfulids.orchestration.config_loader import load_config

MODEL = {
    "id": "llama31_8b_instruct",
    "model_family": "llama3",
    "provider": "local_open_weights",
    "weights": {"revision": "rev-1"},
}


def _ctx() -> GenerationContext:
    attr = AttributionArtifact(
        instance_id="i0",
        feature_names=("Flow Duration", "SYN Flag Count", "Flow Bytes/s"),
        values=(0.8, -0.3, 0.5),
        base_value=0.5,
        method="treeshap",
        exact=True,
        background_policy="tree_path_dependent",
    )
    return GenerationContext(
        instance_id="i0",
        feature_values={"Flow Duration": 123.0, "SYN Flag Count": 5.0, "Flow Bytes/s": 900.0},
        attribution=attr,
        detector_prediction=0.91,
        predicted_class="DoS Hulk",
        dataset_id="cicids2017_corrected",
        metadata={"seed": 7},
    )


def _client(tmp_path):
    return LLMClient(DeterministicStubProvider(), CallLedger(tmp_path), mode="live")


def test_b0_is_deterministic():
    gen = get_generator(load_config("generator", "b0_raw_shap"))
    assert gen.generate(_ctx()).text == gen.generate(_ctx()).text


def test_b1_faithful_by_construction():
    gen = get_generator(load_config("generator", "b1_template"))
    claims = gen.faithful_claims(_ctx())
    assert claims[0].feature == "Flow Duration" and claims[0].direction.sign == 1 and claims[0].rank == 1
    assert claims[1].feature == "Flow Bytes/s" and claims[1].direction.sign == 1
    assert claims[2].feature == "SYN Flag Count" and claims[2].direction.sign == -1
    text = gen.generate(_ctx()).text
    assert "Flow Duration increased" in text and "SYN Flag Count decreased" in text


def test_b2_wired_through_ledger(tmp_path):
    gen = get_generator(load_config("generator", "b2_zeroshot"), llm_client=_client(tmp_path), model_config=MODEL)
    rec = gen.generate(_ctx())
    assert rec.generator_id == "b2_zeroshot"
    assert len(rec.llm_call_ids) == 1  # one logged generation call


def test_b4_abstains_and_degrades_to_b1(tmp_path):
    gen = get_generator(load_config("generator", "b4_vte"), llm_client=_client(tmp_path), model_config=MODEL)
    rec = gen.generate(_ctx())
    # the stub verifier never emits SUPPORTED -> abstain -> B1 fallback (never silence)
    assert rec.abstained is True
    assert rec.fallback_generator_id == "b1_template"
    assert rec.text.startswith("The model classified this flow as DoS Hulk")
    assert len(rec.llm_call_ids) == 2  # draft + verify, both logged
    # queue #2: the abstention now carries a verifier trace (metadata was empty)
    trace = rec.metadata["verifier_trace"]
    assert trace["supported"] is False and trace["reason"]


def test_rule_verifier_reasons():
    """The rule verifier reports WHY it (dis)approved — the abstention trace."""
    from faithfulids.generation.b4_vte.verifier import RuleVerifier

    rv = RuleVerifier()
    rfl = "1. Flow Duration (increases)\n2. SYN Flag Count (decreases)"
    assert rv.verify("Flow Duration is higher than usual.", rfl).reason == "supported"
    assert rv.verify("Nothing relevant here.", rfl).reason == "no_cited_feature"
    assert rv.verify("Anything.", "no evidence lines here").reason == "no_evidence"
    bad = rv.verify("Flow Duration decreased sharply.", rfl)  # evidence says increases
    assert bad.supported is False and bad.reason == "direction_mismatch"
    assert bad.detail["feature"] == "flow duration"


# --------------------------------------------------------------------------- #
# Multi-class score-label wording (GenerationContext.score_label).
# --------------------------------------------------------------------------- #
def _mc_ctx() -> GenerationContext:
    """A K-way context: the attribution explains the PREDICTED class (BENIGN here
    on purpose — the case where attack-framed wording would be false)."""
    c = _ctx()
    return GenerationContext(
        instance_id=c.instance_id, feature_values=c.feature_values,
        attribution=c.attribution, detector_prediction=0.91,
        predicted_class="BENIGN", dataset_id=c.dataset_id,
        metadata=c.metadata, score_label="BENIGN",
    )


class _CapturingClient:
    """Records prompts; returns a fixed response (no ledger, no provider)."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, *, model_config, prompt, params):
        self.prompts.append(prompt)

        class _R:
            text = "stub response"
            request_hash = "0" * 12

        return _R()


def test_binary_rendered_strings_are_frozen():
    """The binary wording is baked into every cached run's LLM request hashes —
    these literals must never drift (token-free replay)."""
    from faithfulids.generation.base import ranked_feature_list, ranked_topk

    rfl = ranked_feature_list(ranked_topk(_ctx().attribution, 2))
    assert "(increases attack score, magnitude 0.8000)" in rfl
    b1 = get_generator(load_config("generator", "b1_template"))
    assert "increased the attack score" in b1.generate(_ctx()).text


def test_b1_multiclass_text_names_the_predicted_class_score():
    """B1 is faithful by construction: on a BENIGN-predicted instance the rendered
    direction must be about the BENIGN score (the class the attribution explains),
    not a false 'attack score'."""
    b1 = get_generator(load_config("generator", "b1_template"))
    text = b1.generate(_mc_ctx()).text
    assert "increased the BENIGN score" in text
    assert "attack score" not in text


def test_ranked_feature_list_renders_the_score_label():
    from faithfulids.generation.base import ranked_feature_list, ranked_topk

    rfl = ranked_feature_list(ranked_topk(_ctx().attribution, 3), "PortScan")
    assert "(increases PortScan score" in rfl and "(decreases PortScan score" in rfl


def test_select_template_picks_by_score_label_and_fails_loudly():
    import pytest

    from faithfulids.generation.base import select_template

    assert select_template("bin", "multi", "attack") == "bin"
    assert select_template("bin", "multi", "DoS") == "multi"
    with pytest.raises(ValueError, match="prompt_multiclass"):
        select_template("bin", None, "DoS")


def test_b3_selects_the_multiclass_prompt_variant():
    client = _CapturingClient()
    gen = get_generator(load_config("generator", "b3_dte_style"), llm_client=client, model_config=MODEL)
    gen.generate(_ctx())      # binary context -> v1.0.0 wording
    gen.generate(_mc_ctx())   # K-way context -> v1.1.0 wording
    binary_prompt, mc_prompt = client.prompts
    assert "likelihood of an attack" in binary_prompt
    assert "increases attack score" in binary_prompt
    assert "likelihood of an attack" not in mc_prompt
    assert "decreased the BENIGN score" in mc_prompt   # instruction line
    assert "(increases BENIGN score" in mc_prompt      # evidence list


def test_b4_multiclass_evidence_still_parses_in_the_rule_verifier():
    """The rule verifier's evidence regex keys on the increases/decreases verbs,
    not the score noun — a class-labelled evidence list must verify unchanged."""
    from faithfulids.generation.b4_vte.verifier import RuleVerifier

    rfl = ("1. Flow Duration (increases BENIGN score, magnitude 0.8000)\n"
           "2. SYN Flag Count (decreases BENIGN score, magnitude 0.3000)")
    rv = RuleVerifier()
    assert rv.verify("Flow Duration is higher than usual.", rfl).reason == "supported"
    bad = rv.verify("Flow Duration decreased sharply.", rfl)
    assert bad.reason == "direction_mismatch"


def test_runner_sets_score_label_from_the_detector_arity():
    """run_cells: binary detectors keep the frozen 'attack' literal; a K-way
    detector passes the class the attribution explains."""
    from faithfulids.framework import ClaimSet, ExplanationRecord, Generator
    from faithfulids.orchestration.runner import Components, InstanceCase, run_cells

    class _Det:
        feature_names = ("Flow Duration", "SYN Flag Count", "Flow Bytes/s")

        def __init__(self, names):
            self.class_names = names

        def predict_proba(self, rows):
            k = len(self.class_names)
            return [[1.0 / k] * k for _ in rows]

        def predicted_class(self, rows):
            return [self.class_names[-1] for _ in rows]

    class _Erasure:
        def erase(self, instance, features):
            return dict(instance)

    class _Extractor:
        extractor_id = "stub"
        extractor_version = "0.0.0"
        prompt_sha256 = "0" * 64

        def extract(self, record):
            return ClaimSet(record.instance_id, (), "stub", "0.0.0", "0" * 64)

    class _RecordingGen(Generator):
        generator_id = "rec"
        llm_dependent = False

        def __init__(self):
            self.score_labels = []

        def generate(self, context):
            self.score_labels.append(context.score_label)
            return ExplanationRecord(instance_id=context.instance_id,
                                     generator_id=self.generator_id, text="t")

    base = _ctx()
    for names, explained, expected in (
        (("BENIGN", "ATTACK"), "ATTACK", "attack"),       # binary: frozen literal
        (("BENIGN", "DoS", "PortScan"), "DoS", "DoS"),    # K-way: explained class
    ):
        attr = AttributionArtifact(
            instance_id="i0", feature_names=base.attribution.feature_names,
            values=base.attribution.values, base_value=0.5, method="stub",
            exact=True, background_policy="stub", explained_class=explained,
        )
        case = InstanceCase(instance_id="i0", feature_values=dict(base.feature_values),
                            attribution=attr, detector_prediction=0.9,
                            predicted_class=explained)
        gen = _RecordingGen()
        run_cells([case], [("rec", gen)],
                  Components(detector=_Det(names), extractor=_Extractor(),
                             erasure=_Erasure(), dataset_id="d",
                             layer1_top_k=3, layer2_k_values=[1]),
                  seed=0)
        assert gen.score_labels == [expected]
