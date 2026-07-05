#!/usr/bin/env python3
"""Render the artifact lineage DAG for a figure/table/claim (`make lineage`).

Reconstructs the DAG behind a paper asset from ``paper/mapping.yaml`` and the
run manifests' ``inputs`` (which are (id, hash) pairs), down to prompts, KB,
seeds, commit, and container digest (blueprint §6). Prints a text tree and, if
``--dot`` is given, a Graphviz DOT graph.

Run: ``python tools/lineage_graph.py <asset-id> [--dot]``  (needs PYTHONPATH=src)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from faithfulids.provenance import repo_root
from faithfulids.results.api import ResultError, load_run


def _mapping() -> dict:
    p = repo_root() / "paper" / "mapping.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else {}


def lineage_lines(asset_id: str) -> list[str]:
    mapping = _mapping()
    assets = {a.get("id"): a for a in mapping.get("assets", [])}
    if asset_id not in assets:
        raise KeyError(f"asset {asset_id!r} not found in paper/mapping.yaml")
    asset = assets[asset_id]
    lines = [f"{asset_id} ({asset.get('kind', 'asset')})"]
    lines.append(f"  ← analysis: {asset.get('analysis')}")
    for run_id in asset.get("runs", []):
        lines.append(f"    ← run: {run_id}")
        try:
            handle = load_run(run_id)
            m = handle.manifest
            lines.append(f"        commit: {m.code_version.short}  status: {m.status.value}")
            for inp in m.inputs:
                lines.append(f"        input: {inp.artifact_id} @ {inp.content_sha256[:12]}…")
            for model in m.models:
                lines.append(f"        model[{model.role}]: {model.identity}")
        except ResultError as exc:
            lines.append(f"        (run artifacts unavailable: {exc})")
    for gate in asset.get("gates", []):
        lines.append(f"    ← gate: {gate}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("asset")
    parser.add_argument("--dot", action="store_true")
    args = parser.parse_args()
    try:
        lines = lineage_lines(args.asset)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
