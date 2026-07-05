"""Attribution base + content-addressed cache (L2).

A common ``AttributionArtifact`` (framework schema) is produced by exact TreeSHAP
or approximate DeepSHAP. Attributions are expensive, so they are cached
**content-addressed** by the hash of everything that produced them (model hash,
data hash, attribution-config hash): a changed input yields a NEW cache key —
never an in-place update (blueprint §6, "nothing is silently regenerated").

Attributor implementations are dispatched lazily by method so importing this
package never pulls in ``shap`` / ``torch``.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from faithfulids.framework import AttributionArtifact
from faithfulids.provenance.hashing import content_address

ATTRIBUTION_MODULES: dict[str, str] = {
    "treeshap": "faithfulids.attribution.treeshap",
    "deepshap": "faithfulids.attribution.deepshap",
}

ARTIFACTS_FILE = "attributions.jsonl"
INPUTS_FILE = "cache_inputs.json"


def get_attributor(method: str, **kwargs: Any):
    """Lazily import and construct the attributor for ``method``."""
    if method not in ATTRIBUTION_MODULES:
        raise KeyError(f"unknown attribution method: {method!r}")
    mod = importlib.import_module(ATTRIBUTION_MODULES[method])
    return mod.build(**kwargs)


def attribution_cache_key(*, model_sha256: str, data_sha256: str, config_sha256: str,
                          background_sha256: str | None = None) -> str:
    """Content-address for an attribution cache entry from all of its inputs."""
    inputs: dict[str, Any] = {
        "model_sha256": model_sha256,
        "data_sha256": data_sha256,
        "attribution_config_sha256": config_sha256,
    }
    if background_sha256 is not None:
        inputs["background_sha256"] = background_sha256
    return content_address(inputs)


class AttributionCache:
    """A content-addressed store of attribution artifacts."""

    def __init__(self, cache_root: str | Path) -> None:
        self.root = Path(cache_root)

    def _entry_dir(self, key: str) -> Path:
        return self.root / key

    def has(self, key: str) -> bool:
        return (self._entry_dir(key) / ARTIFACTS_FILE).is_file()

    def get(self, key: str) -> list[AttributionArtifact] | None:
        path = self._entry_dir(key) / ARTIFACTS_FILE
        if not path.is_file():
            return None  # cache miss => caller computes and puts a NEW entry
        artifacts = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                artifacts.append(AttributionArtifact.from_dict(json.loads(line)))
        return artifacts

    def put(
        self, key: str, artifacts: list[AttributionArtifact], inputs: dict[str, Any]
    ) -> Path:
        d = self._entry_dir(key)
        d.mkdir(parents=True, exist_ok=True)
        (d / ARTIFACTS_FILE).write_text(
            "".join(json.dumps(a.to_dict(), sort_keys=True) + "\n" for a in artifacts),
            encoding="utf-8",
        )
        (d / INPUTS_FILE).write_text(
            json.dumps(inputs, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return d
