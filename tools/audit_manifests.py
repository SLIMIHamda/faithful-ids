#!/usr/bin/env python3
"""Audit every runs/ manifest (CI job `manifest-audit`).

Walks committed run directories and verifies: STATUS is terminal, the manifest
validates, and every declared output hash-verifies (hostile-audit A6). The toy
run (EXP-TOY-001) and cache dirs are skipped — they are regenerable, non-citable
fixtures and are gitignored.

Run: ``python tools/audit_manifests.py``  (needs PYTHONPATH=src)
"""

from __future__ import annotations

import sys
from pathlib import Path

from faithfulids.provenance import read_status, repo_root, verify_outputs


def audit(runs_root: str | Path | None = None) -> list[str]:
    root = Path(runs_root) if runs_root is not None else repo_root() / "runs"
    if not root.is_dir():
        print("manifest-audit: no runs/ directory yet — nothing to audit.")
        return []
    errors: list[str] = []
    audited = 0
    for exp_dir in sorted(root.iterdir()):
        if not exp_dir.is_dir() or exp_dir.name.startswith("_") or exp_dir.name == "EXP-TOY-001":
            continue
        for run_dir in sorted(exp_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            audited += 1
            status = read_status(run_dir)
            if status is None or not status.terminal:
                errors.append(f"{run_dir.name}: STATUS not terminal ({status})")
                continue
            for problem in verify_outputs(run_dir):
                errors.append(f"{run_dir.name}: {problem}")
    if not errors:
        print(f"manifest-audit: OK — {audited} run(s) verified.")
    return errors


def main() -> int:
    errors = audit()
    if errors:
        print("manifest-audit: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
