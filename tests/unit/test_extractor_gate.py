"""EXP-G-001 gate token: written from a scored audit, read by enforce_gates."""

from __future__ import annotations

import json

import pytest

from faithfulids.orchestration.config_loader import load_config
from faithfulids.orchestration.extractor_gate import (
    GATE_ID,
    llm_claims_key,
    write_extractor_gate_run,
)
from faithfulids.orchestration.gates import GateNotPassed, enforce_gates
from faithfulids.orchestration.registry import load_experiment
from faithfulids.orchestration.runner import CellArtifacts, write_run
from faithfulids.provenance import CodeVersion, Status, read_manifest, read_status

CODE = CodeVersion(git_commit="a" * 40, dirty=False)


def _batch(tmp_path, key_field):
    b = tmp_path / "batch"
    (b / "llm_annotation" / "responses" / "P1").mkdir(parents=True)
    items = {"aud-0": {"item_id": "aud-0", "explanation_text": "Flow Duration raises the score.",
                       "candidates": ["Flow Duration"]}}
    (b / "audit_batch.jsonl").write_text(json.dumps(items["aud-0"]) + "\n", encoding="utf-8")
    key = {"aud-0": {"generator_id": "b3_dte_style", key_field: [
        {"feature": "Flow Duration", "direction": "+", "direction_evidence": "llm"},
        {"feature": "PSH Flag Count", "direction": None, "direction_evidence": "default"},
    ]}}
    (b / "audit_key_DO_NOT_SHOW_ANNOTATOR.json").write_text(json.dumps(key), encoding="utf-8")
    (b / "feature_vocabulary.json").write_text('["Flow Duration", "PSH Flag Count"]', encoding="utf-8")
    passes = [b / "llm_annotation" / "responses" / "P1" / "chunk_01.jsonl"]
    passes[0].write_text("{}\n", encoding="utf-8")
    return b, items, key, passes


def _verdict(passed=True):
    r = {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 1, "n_gold": 1, "n_pred": 1}
    return {"results": {"agreed + adjudicated": r}, "passed": passed, "threshold": 0.95,
            "adjudication_can_change_verdict": False, "agreement": 1.0,
            "cohens_kappa": 1.0, "krippendorff_alpha": 1.0, "n_items": 1, "n_cells": 1,
            "annotators": ["P1", "P2"], "n_disputed": 0}


def _token(tmp_path, runs, cfg, verdict=None):
    key_field = llm_claims_key(str(cfg["version"]))
    b, items, key, passes = _batch(tmp_path, key_field)
    return write_extractor_gate_run(
        runs, batch=b, items=items, key=key, claims_key=key_field, extractor_cfg=cfg,
        verdict=verdict or _verdict(), pass_files=passes, adjudication=None, code_version=CODE,
    )


def _g002_token(runs):
    write_run(runs, run_id="EXP-G-002__aaaaaaa__2026-10-03T1200Z", experiment_id="EXP-G-002",
              artifacts=CellArtifacts(), resolved_config={"experiment": "EXP-G-002"},
              code_version=CODE, environment={"environment_hash": "0" * 64}, seeds={},
              inputs=[], models=[], gate="PASSED")


def test_gate_run_is_a_complete_passed_token(tmp_path):
    cfg = load_config("extraction", "eval_extractor")
    run_dir = _token(tmp_path, tmp_path / "runs", cfg)
    assert run_dir.parent.name == GATE_ID
    assert read_status(run_dir) is Status.COMPLETE
    m = read_manifest(run_dir)
    assert m.gate == "PASSED"
    assert [x.role for x in m.models] == ["extractor"]
    assert {i.kind for i in m.inputs} >= {"audit_batch", "audit_key", "annotation"}
    claims = [json.loads(line) for line in
              (run_dir / "artifacts" / "claims.jsonl").read_text(encoding="utf-8").splitlines()]
    assert claims[0]["extractor_version"] == cfg["version"]


def test_tier_a_unlocks_only_with_both_tokens(tmp_path):
    runs = tmp_path / "runs"
    exp = load_experiment("EXP-A-001")
    _token(tmp_path, runs, load_config("extraction", "eval_extractor"))
    with pytest.raises(GateNotPassed, match="EXP-G-002"):
        enforce_gates(exp, runs)
    _g002_token(runs)
    enforce_gates(exp, runs)


def test_token_from_another_extractor_version_does_not_count(tmp_path):
    runs = tmp_path / "runs"
    old = {**load_config("extraction", "eval_extractor"), "version": "0.0.1"}
    _token(tmp_path, runs, old)
    _g002_token(runs)
    with pytest.raises(GateNotPassed, match="must be passed by extractor"):
        enforce_gates(load_experiment("EXP-A-001"), runs)


def test_failed_verdict_writes_a_failed_token_that_unlocks_nothing(tmp_path):
    runs = tmp_path / "runs"
    run_dir = _token(tmp_path, runs, load_config("extraction", "eval_extractor"),
                     verdict=_verdict(passed=False))
    assert read_manifest(run_dir).gate == "FAILED"
    _g002_token(runs)
    with pytest.raises(GateNotPassed):
        enforce_gates(load_experiment("EXP-A-001"), runs)


def test_rule_only_claims_and_sensitivity_scores_are_refused(tmp_path):
    cfg = load_config("extraction", "eval_extractor")
    rule_key = f"extractor_claims_{cfg['version'].replace('.', '_')}"
    b, items, key, passes = _batch(tmp_path, rule_key)
    common = dict(batch=b, items=items, key=key, extractor_cfg=cfg, pass_files=passes,
                  adjudication=None, code_version=CODE)
    with pytest.raises(ValueError, match="LLM path"):
        write_extractor_gate_run(tmp_path / "runs", claims_key=rule_key,
                                 verdict=_verdict(), **common)
    with pytest.raises(ValueError, match="never the verdict"):
        write_extractor_gate_run(tmp_path / "runs", claims_key=llm_claims_key(cfg["version"]),
                                 verdict={**_verdict(), "sensitivity_only": True}, **common)
