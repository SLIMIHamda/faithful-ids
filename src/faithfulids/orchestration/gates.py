"""Gate enforcement (L5).

Gates are first-class experiments (EXP-G-001 extractor audit, EXP-G-002 RQ0
calibration). Orchestration refuses to compute Layer-1 metrics for any run whose
experiment declares a gate dependency without a PASSED run of that gate. This
turns "metrics failing H0 are repaired before the main sweep" into a mechanical
ordering constraint, not a promise.
"""

from __future__ import annotations

from pathlib import Path

from faithfulids.provenance import Status, read_manifest, read_status


class GateNotPassed(RuntimeError):
    """Raised when a required gate has no PASSED, COMPLETE run."""


def _has_passed_run(gate_id: str, runs_root: str | Path) -> bool:
    gate_dir = Path(runs_root) / gate_id
    if not gate_dir.is_dir():
        return False
    for run_dir in gate_dir.iterdir():
        if not run_dir.is_dir():
            continue
        if read_status(run_dir) is not Status.COMPLETE:
            continue
        try:
            manifest = read_manifest(run_dir)
        except FileNotFoundError:
            continue
        if manifest.gate == "PASSED":
            return True
    return False


def enforce_gates(experiment: dict, runs_root: str | Path) -> None:
    """Raise ``GateNotPassed`` unless every declared gate dependency has a
    PASSED run. Experiments with no ``gate_dependencies`` pass trivially."""
    missing = [
        g for g in experiment.get("gate_dependencies", [])
        if not _has_passed_run(g, runs_root)
    ]
    if missing:
        raise GateNotPassed(
            f"experiment {experiment['id']} requires PASSED gate run(s) for {missing}; "
            "Layer-1 metric computation is refused until the gate(s) pass."
        )
