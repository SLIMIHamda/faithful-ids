#!/usr/bin/env python3
"""Emit the environment fingerprint recorded in every run manifest.

The fingerprint is a stable, sorted JSON document plus its sha256. It is the
``environment`` block referenced by ``provenance/manifest.v1.json``:

    lock-file hash, container image digest, hardware (GPU model, driver, cuDNN),
    OS, interpreter.

This module is **pure standard library** on purpose: it must run inside the
minimal container before the scientific stack is imported, and it must never
influence a scientific parameter. Hardware/GPU fields are read from the
environment (populated by the container entrypoint / CI) rather than probed with
a heavy dependency, so the fingerprint is reproducible and side-effect free.

No scientific parameter, path, seed, or model name appears here.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / "uv.lock"


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def collect() -> dict[str, object]:
    """Collect the environment fingerprint fields.

    Container/GPU fields come from environment variables set by the pinned
    container or CI runner. A ``None`` value means "not recorded in this
    environment" — the runner decides whether that is admissible for a given
    reproduction tier (e.g. CPU-only stages tolerate absent GPU fields).
    """
    return {
        "lock_file_sha256": _sha256_file(LOCK_FILE),
        "container_image_digest": os.environ.get("CONTAINER_IMAGE_DIGEST"),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "hardware": {
            "gpu_model": os.environ.get("GPU_MODEL"),
            "driver_version": os.environ.get("GPU_DRIVER_VERSION"),
            "cudnn_version": os.environ.get("CUDNN_VERSION"),
            "cuda_version": os.environ.get("CUDA_VERSION"),
        },
    }


def fingerprint() -> dict[str, object]:
    """Return the collected fields plus the canonical hash of those fields."""
    fields = collect()
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"environment": fields, "environment_hash": digest}


def main() -> int:
    print(json.dumps(fingerprint(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
