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
    # b0's template is f"{feature}={value:+.4f}" — the ':+' spec ALWAYS emits a
    # sign, so a b0 dump never contains an unsigned value. Verified against all
    # 75 numeric values in the EXP-G-001 audit's b0 stratum: 75 signed, 0 not.
    text = (
        "SHAP attribution (top-5) for class benign: Fwd Packet Length Max=-7.9774; "
        "Bwd IAT Total=-1.2186; Flow Duration=+0.5501"
    )
    claims = ext.extract(ExplanationRecord("i0", "b0_raw_shap", text)).claims
    d = {c.feature: c.direction for c in claims}
    assert d["Fwd Packet Length Max"] is Direction.NEGATIVE
    assert d["Bwd IAT Total"] is Direction.NEGATIVE
    assert d["Flow Duration"] is Direction.POSITIVE  # +0.55, sign-only, no word


def test_unsigned_value_after_equals_is_not_a_direction():
    """Extractor 2.1.0 (prereg amendment 0004, attempt 4). The numeric branch
    exists to read b0's SIGNED SHAP dump. b2_zeroshot writes the feature's
    MEASURED VALUE in the same shape — "PSH Flag Count = 1.0" — and while the
    sign was optional that parsed as +1.0, so the extractor read a value as a
    direction: 46 of the 55 false positives in the audit. A value is not an
    attribution, and b0's format string guarantees the sign it relies on."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["PSH Flag Count", "Bwd Header Length"],
    )
    text = ("The flow was classified as **Web Attack** due to the presence of "
            "**PSH Flag Count = 1.0**, and **Bwd Header Length = 40.0**.")
    claims = {c.feature: c for c in ext.extract(
        ExplanationRecord("i0", "b2_zeroshot", text)).claims}
    for f in ("PSH Flag Count", "Bwd Header Length"):
        assert claims[f].direction is None, f"{f} value read as a direction"
        assert claims[f].direction_evidence == "default"


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
    assert claims.extractor_version == "2.1.0"


def test_rule_assisted_recovers_paraphrased_feature_names():
    """Extractor 1.4.0 regression (Qwen3-32B smoke, 2026-07-13): capable models
    paraphrase canonical names ('the maximum forward packet length' for 'Fwd
    Packet Length Max'); exact matching scored 38/60 B3 instances as structural
    zeros. The hash-pinned alias table maps paraphrases to canonical names."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Fwd Packet Length Max", "Init_Win_bytes_forward",
                            "Fwd Packet Length Mean"],
    )
    text = (
        "1. The **maximum forward packet length** was significantly low, which "
        "strongly decreased the likelihood of an attack.\n"
        "2. The **initial window bytes in the forward direction** were also low, "
        "further reducing the attack score.\n"
        "3. The **average forward packet length** was below expected thresholds "
        "for attacks, contributing to a reduced risk assessment."
    )
    d = {c.feature: c.direction
         for c in ext.extract(ExplanationRecord("i0", "b3_dte_style", text)).claims}
    assert d == {"Fwd Packet Length Max": Direction.NEGATIVE,
                 "Init_Win_bytes_forward": Direction.NEGATIVE,
                 "Fwd Packet Length Mean": Direction.NEGATIVE}


def test_rule_assisted_alias_requires_canonical_in_vocabulary():
    """An alias never activates for a feature outside the run's vocabulary, and
    underscore/case normalisation matches canonical names without aliases."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Init_Win_bytes_forward"],
    )
    text = ("The maximum forward packet length was high. "
            "Init Win bytes forward increased the attack score.")
    claims = ext.extract(ExplanationRecord("i0", "b3_dte_style", text)).claims
    feats = [c.feature for c in claims]
    assert feats == ["Init_Win_bytes_forward"]  # normalised match, no out-of-vocab alias
    assert claims[0].direction is Direction.POSITIVE


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
    # not be attributed to it. No cue and no number in the window, so extractor
    # 2.0.0 asserts NO direction (prereg amendment 0004) rather than guessing
    # POSITIVE. The claim is still made: the feature IS mentioned.
    assert d["SYN Flag Count"] is None


def test_rule_assisted_stamps_direction_evidence():
    """Each rule-path claim records HOW its direction was obtained: 'word'
    (explicit cue), 'number' (signed value), or 'default' (fallback guess) —
    the field dsa_asserted / direction_assertion_rate are built on."""
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Flow Duration", "SYN Flag Count", "Flow Bytes/s"],
    )
    text = (
        "Flow Duration increased the attack score. "
        "SYN Flag Count=-1.25. "
        "Flow Bytes/s was typical of this service."
    )
    ev = {c.feature: c.direction_evidence
          for c in ext.extract(ExplanationRecord("i0", "b3_dte_style", text)).claims}
    assert ev == {"Flow Duration": "word", "SYN Flag Count": "number",
                  "Flow Bytes/s": "default"}


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


def test_direction_cues_exclude_polarity_transparent_connectives():
    """Extractor 1.5.0 (prereg amendment 0004). The 300-item audit showed the cue
    lists were too narrow, but widening them is only safe for words that carry
    polarity THEMSELVES.

    "contributed to", "added to", "drove", "supports" inherit polarity from what
    follows, so as bare cues they are wrong about as often as they are right —
    and nearest-cue-wins would let the connective outrank the word carrying the
    sign. A first draft of the expansion included them and this is the case that
    caught it.
    """
    from faithfulids.extraction.extractor import _NEG_WORDS, _POS_WORDS

    transparent = ("add", "contribut", "driv", "support", "toward", "favor")
    for w in transparent:
        assert w not in _POS_WORDS and w not in _NEG_WORDS, (
            f"{w!r} is direction-transparent — it takes its sign from its object, "
            f"so as a cue it mis-signs 'contributing to a reduced risk'"
        )

    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Flow Duration", "Flow Bytes/s"],
    )
    text = ("Flow Duration was long, contributing to a reduced attack score. "
            "Flow Bytes/s was elevated, which amplified the attack score.")
    d = {c.feature: c.direction for c in ext.extract(
        ExplanationRecord("i0", "b3_dte_style", text)).claims}
    # the valenced word decides, not the connective that precedes it
    assert d["Flow Duration"] is Direction.NEGATIVE
    # and the widened positive stems do fire
    assert d["Flow Bytes/s"] is Direction.POSITIVE


def test_extractor_asserts_no_direction_without_evidence():
    """Extractor 2.0.0 (prereg amendment 0004). Where the text gives no direction
    cue and no signed value, the extractor asserts NOTHING rather than falling
    back to POSITIVE.

    The fallback was right often enough to look harmless — "+" is the base rate —
    which is why it survived three instrument revisions until the 300-item
    EXP-G-001 audit scored it against gold: 49 of b2_zeroshot's fallbacks were
    directions the text never asserted, and they counted as claims because the
    artifact had no way to say "the text does not say".

    The claim is still EMITTED: the feature is mentioned, and Layer-1 mention
    precision/recall depend on that. Only the invented sign is withdrawn.
    """
    from faithfulids.framework import ClaimTuple

    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["PSH Flag Count", "Flow Duration"],
    )
    # value description with no stated effect on the score — b2's dominant style
    text = ("A high **PSH Flag Count** (1.0) suggests potential payload manipulation "
            "typical of botnet activity. **Flow Duration** increased the Bot score.")
    claims = {c.feature: c for c in ext.extract(
        ExplanationRecord("i0", "b2_zeroshot", text)).claims}

    assert claims["PSH Flag Count"].direction is None
    assert claims["PSH Flag Count"].direction_evidence == "default"
    # the mention survives — only the sign is withdrawn
    assert set(claims) == {"PSH Flag Count", "Flow Duration"}
    assert claims["Flow Duration"].direction is Direction.POSITIVE
    assert claims["Flow Duration"].direction_evidence == "word"

    # the invariant is enforced, not merely documented, in both directions
    import pytest

    with pytest.raises(ValueError, match="direction is None exactly when"):
        ClaimTuple("X", Direction.POSITIVE, direction_evidence="default")
    with pytest.raises(ValueError, match="direction is None exactly when"):
        ClaimTuple("X", None, direction_evidence="word")
    # and a null direction round-trips through JSON
    c = ClaimTuple("X", None, rank=1, direction_evidence="default")
    assert c.to_dict()["direction"] is None
    assert ClaimTuple.from_dict(c.to_dict()) == c


def test_transparent_connective_counts_only_when_no_valenced_cue():
    """Extractor 2.1.0 (prereg amendment 0004, attempt 4): PRECEDENCE, not
    exclusion.

    2.0.0 excluded direction-transparent connectives outright because
    "contributing to a reduced risk" mis-signed as POSITIVE. The EXP-G-001 audit
    showed that correction was wrong in the other direction: 120 of 143 recall
    misses (84%) were sentences like "Active Min added to the BENIGN score",
    where a reader sees explicit evidence and the engine saw none.

    So a valenced cue wins wherever it sits in the window; a connective counts
    only when the window holds none, and then as POSITIVE — its object is the
    score, and to add to the <class> score is to raise it. Checked against gold:
    right on 99 of the 100 audit cells where this pattern occurs.
    """
    ext = build_extractor(
        _rule_only(), llm_client=None, model_config=None,
        feature_vocabulary=["Active Min", "Idle Mean", "Flow Duration", "Bwd IAT Std"],
    )
    text = (
        "Active Min added to the BENIGN score, showing stable activity. "
        "The Idle Mean also contributed to the DoS score. "
        "Flow Duration was below thresholds, contributing to a reduced attack score. "
        "Bwd IAT Std drove the score downward."
    )
    c = {x.feature: x for x in ext.extract(
        ExplanationRecord("i0", "b5_narrative_vte", text)).claims}

    # no valenced cue in the window -> the connective counts, POSITIVE
    assert c["Active Min"].direction is Direction.POSITIVE
    assert c["Active Min"].direction_evidence == "connective"
    assert c["Idle Mean"].direction is Direction.POSITIVE

    # a valenced cue IS present -> it wins, and the connective must not outrank it
    assert c["Flow Duration"].direction is Direction.NEGATIVE, "regression: 'reduced' must win"
    assert c["Flow Duration"].direction_evidence == "word"
    assert c["Bwd IAT Std"].direction is Direction.NEGATIVE
    assert c["Bwd IAT Std"].direction_evidence == "word"
