"""Tier-A's two steps, locally: generate into the ledger, then replay + LLM-extract + score.

Same light substitutes as test_pilot_execute (RandomForest, stub attributor,
deterministic stub generator); the extractor model is a canned-reply provider.
"""

from __future__ import annotations

import json

import pytest
import yaml

from faithfulids.llm.providers import DeterministicStubProvider
from faithfulids.orchestration.execute import run_pilot
from faithfulids.provenance import Status, read_manifest, read_status

from test_pilot_execute import CV, StubAttributor, _synthetic_multiclass_cicids


class _CannedExtractor:
    """Stands in for the Ollama-served extractor: one claim per text."""

    calls = 0

    def complete(self, prompt, params, *, model):
        type(self).calls += 1
        return '[{"feature": "f0", "direction": "+", "rank": 1, "magnitude": null}]', {"tokens": 9}


def _common(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _synthetic_multiclass_cicids(data_dir / "day1.csv")
    return dict(
        data_dir=data_dir, runs_root=tmp_path / "runs", seed=8005, n_explain=16,
        code_version=CV, detector_id_override="random_forest_multiclass",
        detector_family="random_forest",
        detector_hyperparameters={"n_estimators": 30, "max_depth": 6, "n_jobs": 1},
        attributor=StubAttributor(), llm_id_override="mistral_7b_instruct",
        llm_cache_dir=tmp_path / "gen_ledger",
        extraction_cache_dir=tmp_path / "ext_ledger",
    )


def _ledger_lines(path):
    f = path / "ledger.jsonl"
    return f.read_text(encoding="utf-8").count("\n") if f.is_file() else 0


def test_tier_a_refuses_the_rule_extractor(tmp_path):
    with pytest.raises(ValueError, match="EXP-G-001 certifies"):
        run_pilot("EXP-A-001", data_dir=tmp_path, runs_root=tmp_path / "runs",
                  extraction="rule")


def test_generate_then_score_writes_a_tier_a_run(tmp_path, capsys):
    common = _common(tmp_path)

    # step 1: a zero budget stops before the first call; nothing is lost
    assert run_pilot("EXP-A-001", extraction="none", generation_budget_s=0,
                     llm_provider=DeterministicStubProvider(), **common) is None
    assert "PARTIAL: 0/" in capsys.readouterr().out
    assert run_pilot("EXP-A-001", extraction="none",
                     llm_provider=DeterministicStubProvider(), **common) is None
    assert "generation COMPLETE" in capsys.readouterr().out
    n_calls = _ledger_lines(tmp_path / "gen_ledger")
    assert n_calls > 0
    assert not (tmp_path / "runs" / "EXP-A-001").exists()  # no claims, no run

    # resuming re-uses the ledger instead of calling the model again
    run_pilot("EXP-A-001", extraction="none", llm_provider=DeterministicStubProvider(), **common)
    assert _ledger_lines(tmp_path / "gen_ledger") == n_calls

    # step 2: no generator provider at all; the extractor model is live
    _CannedExtractor.calls = 0
    run_dir = run_pilot("EXP-A-001", llm_mode="replay", extraction="llm",
                        extraction_provider=_CannedExtractor(), **common)
    assert read_status(run_dir) is Status.COMPLETE
    assert _CannedExtractor.calls > 0
    resolved = yaml.safe_load((run_dir / "config.resolved.yaml").read_text(encoding="utf-8"))
    assert resolved["extractor"]["mode"] == "llm_assisted"
    assert resolved["llm_mode"] == "replay"
    assert resolved["instrument_gaps"] and "pilot_note" not in resolved
    ext = [m for m in read_manifest(run_dir).models if m.role == "extractor"]
    assert ext and ext[0].identity.endswith(".gguf@3eca3b8f6d7b")
    claims = [json.loads(line) for line in
              (run_dir / "artifacts" / "claims.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {c["direction_evidence"] for cs in claims for c in cs["claims"]} == {"llm"}
    # amendment 0007: every run reports how many generations stopped at the cap
    metrics = [json.loads(line) for line in
               (run_dir / "artifacts" / "metrics.jsonl").read_text(encoding="utf-8").splitlines()]
    cap = [m for m in metrics if m["metric"] == "reply_cap_hit_rate"]
    assert len(cap) == 1 and cap[0]["grouping"]["n_calls"] > 0

    # a re-score replays extraction from its own ledger too: no new model calls
    calls = _CannedExtractor.calls
    run_pilot("EXP-A-001", llm_mode="replay", extraction="llm",
              extraction_provider=_CannedExtractor(), **{**common, "runs_root": tmp_path / "r2"})
    assert _CannedExtractor.calls == calls


def test_cli_needs_a_step_and_scoring_needs_the_gates(tmp_path, monkeypatch, capsys):
    import argparse

    from faithfulids.orchestration import cli
    from faithfulids.orchestration.gates import GateNotPassed

    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)  # empty runs/: no tokens
    monkeypatch.setenv("FAITHFULIDS_DATA_DIR", str(tmp_path))
    args = argparse.Namespace(experiment="EXP-A-001")
    monkeypatch.delenv("FAITHFULIDS_PHASE", raising=False)
    assert cli.cmd_run(args) == 2
    assert "two steps" in capsys.readouterr().err
    monkeypatch.setenv("FAITHFULIDS_PHASE", "score")
    with pytest.raises(GateNotPassed):
        cli.cmd_run(args)
