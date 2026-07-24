"""The READ-ONLY results API (L5).

The ONLY ``src`` module ``analysis/`` may import. Loads ``runs/**`` by run id,
verifies output hashes against the manifest, and exposes no execution capability
(import-linter edge 4: analysis can never rerun experiments). Imports only L0
(``provenance``) and stdlib/yaml — never ``orchestration``, ``generation``, or
``llm``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from faithfulids.provenance import (
    Manifest,
    Status,
    read_manifest,
    read_status,
    repo_root,
    verify_outputs,
)


class ResultError(RuntimeError):
    """Raised on any results-API failure (missing run, hash mismatch)."""


def default_runs_root() -> Path:
    return repo_root() / "runs"


@dataclass(frozen=True)
class RunHandle:
    run_dir: Path
    manifest: Manifest
    status: Status | None


def find_run_dir(run_id: str, runs_root: str | Path | None = None) -> Path:
    root = Path(runs_root) if runs_root is not None else default_runs_root()
    if not root.is_dir():
        raise ResultError(f"runs root not found: {root}")
    for exp_dir in root.iterdir():
        if exp_dir.is_dir():
            cand = exp_dir / run_id
            if cand.is_dir():
                return cand
    raise ResultError(f"run not found: {run_id}")


def load_run(run_id: str, runs_root: str | Path | None = None, *, verify: bool = True) -> RunHandle:
    d = find_run_dir(run_id, runs_root)
    manifest = read_manifest(d)
    status = read_status(d)
    if verify:
        problems = verify_outputs(d)
        if problems:
            raise ResultError(f"hash verification failed for {run_id}: {problems}")
    return RunHandle(run_dir=d, manifest=manifest, status=status)


def load_metrics(run_id: str, runs_root: str | Path | None = None) -> list[dict]:
    """Return the per-instance metric rows for a run (hash-verified first)."""
    handle = load_run(run_id, runs_root)  # verifies output hashes
    path = handle.run_dir / "artifacts" / "metrics.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_extractor_version(run_id: str, runs_root: str | Path | None = None) -> str | None:
    """The extractor instrument version a run's claims were produced with.

    Read from the run's own claims (every ``ClaimSet`` stamps it), so it is
    recoverable for runs written before any run-level record existed — which is
    the point: cross-run aggregation has to be checkable on the artifacts that
    already exist, not only on ones produced after the check was added.
    ``None`` when the run has no claims.
    """
    handle = load_run(run_id, runs_root)
    path = handle.run_dir / "artifacts" / "claims.jsonl"
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:  # first record only — the version is constant within a run
            if line.strip():
                return json.loads(line).get("extractor_version")
    return None


def list_runs(experiment_id: str, runs_root: str | Path | None = None) -> list[str]:
    root = Path(runs_root) if runs_root is not None else default_runs_root()
    d = root / experiment_id
    return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.is_dir() else []


def is_complete_and_verified(run_id: str, runs_root: str | Path | None = None) -> bool:
    try:
        handle = load_run(run_id, runs_root, verify=True)
    except ResultError:
        return False
    return handle.status is Status.COMPLETE and handle.manifest.status is Status.COMPLETE
