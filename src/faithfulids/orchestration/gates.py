"""Gate enforcement (L5).

Gates are first-class experiments (EXP-G-001 extractor audit, EXP-G-002 RQ0
calibration). Orchestration refuses to compute Layer-1 metrics for any run whose
experiment declares a gate dependency without a PASSED run of that gate. This
turns "metrics failing H0 are repaired before the main sweep" into a mechanical
ordering constraint, not a promise.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from faithfulids.provenance import Status, read_manifest, read_status

#: The extractor audit. Its token certifies one extractor version (see
#: ``orchestration.extractor_gate``), so it is matched against the version the
#: dependent experiment would extract with.
EXTRACTOR_GATE = "EXP-G-001"


class GateNotPassed(RuntimeError):
    """Raised when a required gate has no PASSED, COMPLETE run."""


def _token_extractor_version(run_dir: Path) -> str | None:
    path = run_dir / "config.resolved.yaml"
    if not path.is_file():
        return None
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return str((cfg.get("extractor") or {}).get("version") or "") or None


def _has_passed_run(gate_id: str, runs_root: str | Path, *,
                    extractor_version: str | None = None) -> bool:
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
        if manifest.gate != "PASSED":
            continue
        if extractor_version is not None and _token_extractor_version(run_dir) != extractor_version:
            continue
        return True
    return False


def _extractor_version(experiment: dict) -> str | None:
    ref = (experiment.get("config_refs") or {}).get("extraction")
    if not ref:
        return None
    from faithfulids.orchestration.config_loader import load_config

    return str(load_config("extraction", ref.split(":", 1)[1])["version"])


def enforce_gates(experiment: dict, runs_root: str | Path) -> None:
    """Raise ``GateNotPassed`` unless every declared gate dependency has a
    PASSED run. Experiments with no ``gate_dependencies`` pass trivially.

    An EXP-G-001 token counts only if it was earned by the extractor version
    the experiment's ``config_refs.extraction`` declares today: an audit of an
    older instrument says nothing about the one that would run."""
    deps = experiment.get("gate_dependencies", [])
    version = _extractor_version(experiment) if EXTRACTOR_GATE in deps else None
    missing = [
        g for g in deps
        if not _has_passed_run(g, runs_root,
                               extractor_version=version if g == EXTRACTOR_GATE else None)
    ]
    if missing:
        detail = (f" ({EXTRACTOR_GATE} must be passed by extractor {version})"
                  if version and EXTRACTOR_GATE in missing else "")
        raise GateNotPassed(
            f"experiment {experiment['id']} requires PASSED gate run(s) for {missing}"
            f"{detail}; Layer-1 metric computation is refused until the gate(s) pass."
        )
