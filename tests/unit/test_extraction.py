"""Extractor (firewall side B): rule-assisted parsing recovers B1's faithful claims."""

from __future__ import annotations

from faithfulids.extraction import build as build_extractor
from faithfulids.framework import (
    AttributionArtifact,
    Direction,
    ExplanationRecord,
    GenerationContext,
)
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


def _rule_only():
    """Extractor in deterministic rule-only mode (no LLM), as the pilot runs it."""
    extcfg = load_config("extraction", "eval_extractor")
    return extcfg


def test_rule_assisted_reads_numeric_sign_from_raw_shap_dump():
    """B0 dumps raw SHAP as 'Feature=<signed>' with no direction word; the sign
    must come from the number, not default to POSITIVE (else DSA collapses)."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Fwd Packet Length Max", "Bwd IAT Total", "Flow Duration"],
    )
    text = (
        "SHAP attribution (top-5) for class benign: Fwd Packet Length Max=-7.9774; "
        "Bwd IAT Total=-1.2186; Flow Duration=0.5501"
    )
    claims = ext.extract(ExplanationRecord("i0", "b0_raw_shap", text)).claims
    d = {c.feature: c.direction for c in claims}
    assert d["Fwd Packet Length Max"] is Direction.NEGATIVE
    assert d["Bwd IAT Total"] is Direction.NEGATIVE
    assert d["Flow Duration"] is Direction.POSITIVE  # +0.55, sign-only, no word


def test_rule_assisted_masks_substring_feature_collisions():
    """A shorter feature name that occurs *inside* a longer one must not also be
    claimed (residual-span guard) — CICIDS has 'Packet Length Mean' ⊂ 'Fwd
    Packet Length Mean'."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Fwd Packet Length Mean", "Packet Length Mean", "Flow Duration"],
    )
    text = "Fwd Packet Length Mean=-1.5116; Flow Duration=0.55"
    feats = [c.feature for c in ext.extract(ExplanationRecord("i0", "b0_raw_shap", text)).claims]
    assert "Fwd Packet Length Mean" in feats
    assert "Flow Duration" in feats
    assert "Packet Length Mean" not in feats  # masked: only matched inside the longer name
