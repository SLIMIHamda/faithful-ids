"""Determinism gate: same seed -> byte-identical toy-pipeline outputs.

This is the test the ``determinism-smoke`` CI job runs (twice, into separate run
roots) to prove that every CPU stage is reproducible to the byte.
"""

from __future__ import annotations

from faithfulids.orchestration.toy_pipeline import run_toy
from faithfulids.provenance import CodeVersion

CV = CodeVersion("0" * 40, dirty=False)


def test_same_seed_produces_byte_identical_artifacts(tmp_path):
    a = run_toy(tmp_path / "a", code_version=CV, seed=7002)
    b = run_toy(tmp_path / "b", code_version=CV, seed=7002)
    for name in ("metrics.jsonl", "explanations.jsonl", "claims.jsonl"):
        assert (a / "artifacts" / name).read_bytes() == (b / "artifacts" / name).read_bytes(), (
            f"{name} differs between identical-seed runs"
        )


def test_different_seed_changes_llm_dependent_outputs(tmp_path):
    a = run_toy(tmp_path / "a", code_version=CV, seed=7002)
    b = run_toy(tmp_path / "b", code_version=CV, seed=9999)
    # the deterministic stub encodes the seed, so B2's explanations differ
    assert (a / "artifacts" / "explanations.jsonl").read_bytes() != (
        b / "artifacts" / "explanations.jsonl"
    ).read_bytes()
