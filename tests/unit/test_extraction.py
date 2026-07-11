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


def test_rule_assisted_reads_participle_direction_words():
    """Extractor 1.2.0 regression (blind audit 2026-07-11): Qwen3-8B's B4 writes
    'has a decreasing effect on the attack score' — the participle matched no
    1.1.0 direction word and fell to the default-POSITIVE branch, mis-signing
    63/150 instances (the entire apparent b4@8B DSA regression, Branch 2)."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=[
            "Init_Win_bytes_forward", "Bwd Packets/s", "Total Length of Fwd Packets",
            "Bwd Header Length",
        ],
    )
    text = (
        "- **Init_Win_bytes_forward** has a decreasing effect on the attack score.\n"
        "- **Bwd Packets/s** has an increasing effect on the attack score.\n"
        "- **Total Length of Fwd Packets** is lowering the attack score.\n"
        "- **Bwd Header Length** is reducing the score, consistent with benign traffic.\n"
    )
    d = {c.feature: c.direction
         for c in ext.extract(ExplanationRecord("i0", "b4_vte", text)).claims}
    assert d["Init_Win_bytes_forward"] is Direction.NEGATIVE
    assert d["Bwd Packets/s"] is Direction.POSITIVE
    assert d["Total Length of Fwd Packets"] is Direction.NEGATIVE
    assert d["Bwd Header Length"] is Direction.NEGATIVE


def test_extractor_version_is_stamped_current():
    """Claims must carry the instrument version the config declares — analyses
    assert extractor-version consistency before tabulating across runs."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Flow Duration"],
    )
    claims = ext.extract(ExplanationRecord("i0", "b1_template", "Flow Duration increased."))
    assert claims.extractor_version == "1.3.0"


def test_rule_assisted_reads_tail_position_direction_words():
    """Extractor 1.3.0 regression: Mistral-B4 writes 'Feature: <long value
    clause>, which decreases the attack score' — under the fixed 60-char window
    the tail cue was never read (73/176 mismatches in the 2026-07-11 audit
    follow-up). The window is now sentence-bounded."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Total Length of Fwd Packets", "Bwd Packets/s"],
    )
    text = (
        "Total Length of Fwd Packets: The total length of forward packets is "
        "significantly shorter than usual, which decreases the attack score.\n"
        "Bwd Packets/s: The rate of backward packets is far above the typical "
        "range for this service, a pattern that raises the attack score."
    )
    d = {c.feature: c.direction
         for c in ext.extract(ExplanationRecord("i0", "b4_vte", text)).claims}
    assert d["Total Length of Fwd Packets"] is Direction.NEGATIVE
    assert d["Bwd Packets/s"] is Direction.POSITIVE


def test_rule_assisted_nearest_direction_cue_wins():
    """With sentence-length windows one span can contain both stems; the cue
    nearest the feature is the claimed direction, and the window must not leak
    into the NEXT sentence's cues."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Flow Duration", "SYN Flag Count"],
    )
    text = (
        "Flow Duration increases the attack score, unlike most benign flows "
        "where it shows decreasing values. Overall the remaining indicators "
        "lower the score.\n"
        "SYN Flag Count stayed in range. It increases in floods, but not here."
    )
    d = {c.feature: c.direction
         for c in ext.extract(ExplanationRecord("i0", "b3_dte_style", text)).claims}
    assert d["Flow Duration"] is Direction.POSITIVE     # nearest cue: "increases"
    # window ends at "stayed in range." — the next sentence's "increases" must
    # not be attributed to it; no cue + no number => default POSITIVE, which is
    # exactly the case option 1b would turn into direction=None.
    assert d["SYN Flag Count"] is Direction.POSITIVE


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
