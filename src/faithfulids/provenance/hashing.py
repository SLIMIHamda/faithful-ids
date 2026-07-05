"""Content hashing — the primitive behind every manifest and cache key (L0).

Everything that must be reproducible is addressed by the sha256 of its
*canonical* bytes. Canonicalisation (sorted keys, tight separators, UTF-8) means
two logically-equal JSON documents hash identically regardless of key order or
whitespace — a prerequisite for "nothing silently regenerates" (a cache entry is
keyed by the hash of *all* its inputs).

Pure standard library.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_CHUNK = 1 << 20  # 1 MiB


def canonical_json(obj: Any) -> str:
    """Deterministic JSON string: sorted keys, no incidental whitespace."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_json(obj: Any) -> str:
    """sha256 of the canonical JSON encoding of ``obj``."""
    return sha256_text(canonical_json(obj))


def sha256_file(path: str | Path) -> str:
    """Streaming sha256 of a file's bytes (handles large payloads)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def content_address(inputs: dict[str, Any]) -> str:
    """A content-address for a cache entry keyed by *all* of its inputs.

    ``inputs`` maps a stable name (e.g. ``"model_sha"``, ``"data_sha"``,
    ``"attribution_config_sha"``) to a hashable, JSON-serialisable value. A
    change to any input yields a different address — a new cache key, never an
    in-place update (blueprint §6 "nothing is silently regenerated").
    """
    return sha256_json(inputs)
