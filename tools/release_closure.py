#!/usr/bin/env python3
"""Verify the release bundle has no dangling references (`make release`).

Every run id cited by an analysis config (enumerated) or ``paper/mapping.yaml``
must resolve to a run present in ``runs/`` (or be declared as an externally
deposited artifact). Guarantees closure of the deposited snapshot (blueprint §8
A7 / release step 6). Pre-experiment, with no citations, this passes.

Run: ``python tools/release_closure.py``  (needs PYTHONPATH=src)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from faithfulids.provenance import repo_root
from faithfulids.results.api import find_run_dir, ResultError


def _cited_run_ids() -> set[str]:
    root = repo_root()
    ids: set[str] = set()
    mapping_p = root / "paper" / "mapping.yaml"
    if mapping_p.is_file():
        mapping = yaml.safe_load(mapping_p.read_text(encoding="utf-8")) or {}
        for asset in mapping.get("assets", []):
            ids.update(asset.get("runs", []))
    for cfg_p in (root / "analysis" / "configs").glob("*.yaml"):
        cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8")) or {}
        ids.update(cfg.get("run_ids", []) or [])
    return ids


def dangling() -> list[str]:
    missing: list[str] = []
    for run_id in sorted(_cited_run_ids()):
        try:
            find_run_dir(run_id)
        except ResultError:
            missing.append(run_id)
    return missing


def main() -> int:
    missing = dangling()
    if missing:
        print("release-closure: FAILED — cited run ids not present in runs/:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1
    print("release-closure: OK — no dangling run references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
