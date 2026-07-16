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
from typing import Any, Sequence

from faithfulids.framework import AttributionArtifact
from faithfulids.provenance.hashing import content_address

ATTRIBUTION_MODULES: dict[str, str] = {
    "treeshap": "faithfulids.attribution.treeshap",
    "deepshap": "faithfulids.attribution.deepshap",
}

ARTIFACTS_FILE = "attributions.jsonl"
INPUTS_FILE = "cache_inputs.json"


def select_predicted_class_shap(values: Any, base: Any, class_index: Sequence[int]):
    """Pick each instance's PREDICTED-class SHAP vector + base value out of a
    multi-class attributor output (queue #5.3).

    A multi-class tree model has one attribution PER CLASS; an explanation is only
    meaningful about the class the detector actually predicted, so we select that
    column per instance and keep the downstream contract at one vector per
    instance. ``values`` is either a list of K arrays shaped ``(n, F)`` or one
    ``(n, F, K)`` array — both shapes SHAP emits — and ``base`` is the per-class
    expected value. Returns ``(values_2d (n,F), base_per_instance (n,))``.

    Pure + numpy-only on purpose: ``shap`` is absent off-Kaggle, so this keeps the
    selection logic unit-testable offline.
    """
    import numpy as np

    if isinstance(values, list):
        per_class = [np.asarray(v, dtype=float) for v in values]
    else:
        arr = np.asarray(values, dtype=float)
        if arr.ndim != 3:
            raise ValueError(
                f"expected per-class SHAP (list of (n,F) or one (n,F,K) array); got {arr.shape}"
            )
        per_class = [arr[:, :, k] for k in range(arr.shape[2])]

    n = per_class[0].shape[0]
    if len(class_index) != n:
        raise ValueError(f"class_index has {len(class_index)} entries for {n} instances")
    for k in class_index:
        if not 0 <= k < len(per_class):
            raise ValueError(f"class index {k} out of range for {len(per_class)} SHAP classes")

    b = np.ravel(np.asarray(base, dtype=float))
    out_vals = np.array([per_class[class_index[i]][i] for i in range(n)], dtype=float)
    out_base = np.array(
        [b[class_index[i]] if b.size > 1 else b[0] for i in range(n)], dtype=float
    )
    return out_vals, out_base


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
