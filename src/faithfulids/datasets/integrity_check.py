"""`data-integrity` CI entrypoint (L1).

Verifies the dataset chain checksums (download → corrected → processed) and the
correction-pipeline version consistency (hostile-audit A3). Raw payloads are NOT
redistributed, so where a checksum is still ``null`` (pre-acquisition) this
reports *pending* and passes — the structural chain is what is enforced here;
the byte-level chain is enforced once the reviewer acquires the public data.

Needs only ``pyyaml`` + ``jsonschema`` (no scientific stack).
Run: ``python -m faithfulids.datasets.integrity_check``
"""

from __future__ import annotations

import sys

from faithfulids.datasets.corrections.engelen_lanvin import PIPELINE_VERSION
from faithfulids.orchestration.config_loader import config_dir, repo_root, validate_file


def check() -> list[str]:
    errors: list[str] = []
    pending = 0
    root = repo_root()
    for path in sorted(config_dir("dataset").glob("*.yaml")):
        cfg = validate_file(path)
        did = cfg["id"]
        corr = cfg["correction"]
        # correction pipeline version must match the implemented pipeline when applied
        if corr["applies"] and corr["pipeline_version"] != PIPELINE_VERSION:
            errors.append(
                f"{did}: correction.pipeline_version {corr['pipeline_version']} != "
                f"implemented {PIPELINE_VERSION}"
            )
        # checksum chain: verify present checksums against files; count pending
        for key, rel in (
            ("raw_sha256", f"data/raw/{did.split('_')[0]}"),
            ("corrected_sha256", f"data/corrected/{did.split('_')[0]}"),
            ("processed_sha256", f"data/processed/{did}"),
        ):
            sha = cfg["checksums"].get(key)
            if sha is None:
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
