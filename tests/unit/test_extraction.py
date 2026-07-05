"""Extractor (firewall side B): rule-assisted parsing recovers B1's faithful claims."""

from __future__ import annotations

from faithfulids.extraction import build as build_extractor
from faithfulids.framework import AttributionArtifact, Direction, GenerationContext
from faithfulids.generation import get_generator
from faithfulids.llm import CallLedger, LLMClient
from faithfulids.llm.providers import DeterministicStubProvider
from faithfulids.orchestration.config_loader import load_config


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
        detector_prediction=0.9,
        predicted_class="DoS Hulk",
        dataset_id="cicids2017_corrected",
        metadata={"seed": 0},
    )


def test_rule_assisted_extraction_recovers_b1_directions(tmp_path):
    b1 = get_generator(load_config("generator", "b1_template"))
    explanation = b1.generate(_ctx())

    extcfg = load_config("extraction", "eval_extractor")
    model = {**extcfg["model"], "id": extcfg["id"]}
    client = LLMClient(DeterministicStubProvider(), CallLedger(tmp_path), mode="live")
    extractor = build_extractor(
        extcfg, llm_client=client, model_config=model,
        feature_vocabulary=["Flow Duration", "SYN Flag Count", "Flow Bytes/s"],
    )
    claims = extractor.extract(explanation)
    pairs = {(c.feature, c.direction) for c in claims.claims}
    assert ("Flow Duration", Direction.POSITIVE) in pairs
    assert ("SYN Flag Count", Direction.NEGATIVE) in pairs
    assert claims.extractor_id == "eval_extractor"
    assert len(claims.prompt_sha256) == 64
