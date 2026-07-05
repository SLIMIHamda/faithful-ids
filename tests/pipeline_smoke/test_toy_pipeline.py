"""End-to-end 5-instance toy pipeline: completeness, manifests, results API, gates."""

from __future__ import annotations

import pytest

from faithfulids.orchestration.gates import GateNotPassed, enforce_gates
from faithfulids.orchestration.registry import load_experiment
from faithfulids.orchestration.toy_pipeline import run_toy
from faithfulids.provenance import CodeVersion, Status, read_manifest, read_status, verify_outputs
from faithfulids.results import ResultError, is_complete_and_verified, load_metrics, load_run

CV = CodeVersion("0" * 40, dirty=False)


def test_toy_run_is_complete_and_verifiable(tmp_path):
    run_dir = run_toy(tmp_path, code_version=CV, seed=7002)
    assert read_status(run_dir) is Status.COMPLETE
    assert read_manifest(run_dir).status is Status.COMPLETE
    assert verify_outputs(run_dir) == []

    run_id = run_dir.name
    handle = load_run(run_id, runs_root=tmp_path)
    assert handle.status is Status.COMPLETE
    rows = load_metrics(run_id, runs_root=tmp_path)
    assert any(r["layer"] == "layer1" for r in rows)
    assert any(r["layer"] == "layer2" for r in rows)
    assert is_complete_and_verified(run_id, runs_root=tmp_path)


def test_metric_rows_encode_generator_blindness(tmp_path):
    run_dir = run_toy(tmp_path, code_version=CV, seed=7002)
    rows = load_metrics(run_dir.name, runs_root=tmp_path)
    # Layer-2 (model-level) rows carry NO generator identity; Layer-1 do (attached
    # downstream, post-computation).
    assert all("generator_id" not in r["grouping"] for r in rows if r["layer"] == "layer2")
    assert all("generator_id" in r["grouping"] for r in rows if r["layer"] == "layer1")


def test_gate_enforcement_blocks_ungated_run(tmp_path):
    # EXP-A-001 declares gate dependencies; with no PASSED gate runs it is refused.
    with pytest.raises(GateNotPassed):
        enforce_gates(load_experiment("EXP-A-001"), tmp_path)
    # EXP-TOY-001 has no gate dependencies -> passes trivially.
    enforce_gates(load_experiment("EXP-TOY-001"), tmp_path)


def test_tamper_breaks_hash_verification(tmp_path):
    run_dir = run_toy(tmp_path, code_version=CV, seed=7002)
    (run_dir / "artifacts" / "metrics.jsonl").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ResultError):
        load_run(run_dir.name, runs_root=tmp_path)
