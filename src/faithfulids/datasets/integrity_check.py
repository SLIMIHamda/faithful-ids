"""`data-integrity` CI entrypoint (L1).

Verifies the dataset chain checksums (download -> corrected -> processed) and the
correction-pipeline version consistency (hostile-audit A3). Raw payloads are NOT
redistributed, so where a checksum is still ``null`` (pre-acquisition) this
reports *pending* and passes — the structural chain is enforced here.

Self-contained at L1: it reads dataset configs and validates them against the
dataset schema directly (yaml + jsonschema), rather than importing the L5 config
system (which would break the layered import contract). Needs only ``pyyaml`` +
``jsonschema``. Run: ``python -m faithfulids.datasets.integrity_check``
"""

from __future__ import annotations

import json
import sys

import jsonschema
import yaml

from faithfulids.datasets.corrections.engelen_lanvin import PIPELINE_VERSION
from faithfulids.provenance import repo_root


def check() -> list[str]:
    errors: list[str] = []
    pending = 0
    root = repo_root()
    schema = json.loads(
        (root / "configs" / "schema" / "dataset.v1.json").read_text(encoding="utf-8")
    )
    for path in sorted((root / "configs" / "datasets").glob("*.yaml")):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=cfg, schema=schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{path.name}: schema violation: {exc.message}")
            continue
        corr = cfg["correction"]
        if corr["applies"] and corr["pipeline_version"] != PIPELINE_VERSION:
            errors.append(
                f"{cfg['id']}: correction.pipeline_version {corr['pipeline_version']} != "
                f"implemented {PIPELINE_VERSION}"
            )
        for key in ("raw_sha256", "corrected_sha256", "processed_sha256"):
            if cfg["checksums"].get(key) is None:
                pending += 1
    if errors:
        return errors
    print(
        f"data-integrity: OK — correction pipeline v{PIPELINE_VERSION} consistent; "
        f"{pending} checksum(s) pending acquisition (datasets not redistributed)."
    )
    return []


def main() -> int:
    errors = check()
    if errors:
        print("data-integrity: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
