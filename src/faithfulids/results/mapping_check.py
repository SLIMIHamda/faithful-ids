"""`mapping-completeness` CI entrypoint (L5).

Every figure/table/claim in ``paper/mapping.yaml`` must resolve to COMPLETE,
non-exploratory, hash-verifying runs (hostile-audit A7). Until the mapping exists
(paper phase), the check passes trivially — there is nothing to verify.

Needs only ``pyyaml`` + the read-only results API.
"""

from __future__ import annotations

import sys

import yaml

from faithfulids.provenance import repo_root
from faithfulids.results.api import ResultError, load_run


def check(runs_root=None) -> list[str]:
    errors: list[str] = []
    mapping_path = repo_root() / "paper" / "mapping.yaml"
    if not mapping_path.is_file():
        print("mapping-completeness: no paper/mapping.yaml yet — nothing to verify.")
        return []
    mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    assets = mapping.get("assets", [])
    for asset in assets:
        aid = asset.get("id", "<?>")
        if asset.get("exploratory"):
            errors.append(f"{aid}: headline asset references an exploratory experiment")
        for run_id in asset.get("runs", []):
            try:
                handle = load_run(run_id, runs_root)
            except ResultError as exc:
                errors.append(f"{aid}: {exc}")
                continue
            if handle.manifest.status.value != "COMPLETE":
                errors.append(f"{aid}: run {run_id} is not COMPLETE")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("mapping-completeness: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("mapping-completeness: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
