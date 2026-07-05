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
