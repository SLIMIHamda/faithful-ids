"""Config system: schema validation, reference resolution, prompt/KB integrity."""

from __future__ import annotations

import pytest

from faithfulids.orchestration.config_loader import ConfigError, load_config
from faithfulids.orchestration.references import (
    resolve_kb,
    resolve_reference,
    verify_prompt,
)
from faithfulids.orchestration.validate_configs import validate_all


def test_all_configs_valid_and_references_resolve():
    errors = validate_all()
    assert errors == [], "config validation problems:\n" + "\n".join(errors)


def test_llm_dependent_flag_present_and_typed():
    for gid, expected in [
        ("b0_raw_shap", False),
        ("b1_template", False),
        ("b2_zeroshot", True),
        ("b3_dte_style", True),
        ("b4_vte", True),
    ]:
        cfg = load_config("generator", gid)
        assert cfg["llm_dependent"] is expected


def test_exploratory_flag_on_cti_experiment():
    from faithfulids.orchestration.registry import load_experiment

    exp = load_experiment("EXP-X-001")
    assert exp["flags"]["exploratory"] is True
    assert exp["flags"]["headline_eligible"] is False


def test_prompt_hash_verification_detects_tamper():
    # a correct reference verifies
    good = {
        "name": "b2_zeroshot",
        "version": "1.0.0",
        "sha256": "fdff0dc355f2135960f616f0c09a85aa9d0a96b4b7afed37164322ca27da55ae",
    }
    assert verify_prompt(good) == good["sha256"]
    bad = dict(good, sha256="0" * 64)
    with pytest.raises(ConfigError):
        verify_prompt(bad)


def test_kb_reference_version_drift_is_rejected():
    assert resolve_kb("kb:cicids2017@1.0.0") == {"name": "cicids2017", "version": "1.0.0"}
    with pytest.raises(ConfigError):
        resolve_kb("kb:cicids2017@9.9.9")
    with pytest.raises(ConfigError):
        resolve_kb("kb:not_a_dataset@1.0.0")


def test_seed_reference_resolves_to_section():
    section = resolve_reference("seeds:splits")
    assert section["cicids2017_corrected"] == 20250101


def test_decision_threshold_reference_resolves():
    thr = resolve_reference("statistics:decision_thresholds:verifier_threshold")
    assert thr["value"] == [0.3, 0.5, 0.7]
