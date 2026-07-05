"""Prompt registry loader with hash verification (L2).

Prompts are frozen, hash-addressed scientific instruments. Loading one verifies
the file on disk against ``prompts/REGISTRY.json`` (and, if given, against the
sha256 declared by the calling config) so a drifted prompt can never be silently
used. Lives at L2 so L3 generators/extractor can load prompts without importing
the L5 config layer.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from faithfulids.provenance import repo_root, sha256_file


class PromptError(RuntimeError):
    """Raised on any prompt registry / hash failure."""


@lru_cache(maxsize=1)
def _registry() -> dict[str, Any]:
    path = repo_root() / "prompts" / "REGISTRY.json"
    return json.loads(path.read_text(encoding="utf-8"))["prompts"]


def prompt_path(name: str, version: str) -> Path:
    registry = _registry()
    if name not in registry or version not in registry[name]:
        raise PromptError(f"prompt not registered: {name}@{version}")
    return repo_root() / registry[name][version]["path"]


def load_prompt(name: str, version: str, *, expected_sha256: str | None = None) -> str:
    """Return the prompt text, verifying its hash against the registry and file."""
    registry = _registry()
    if name not in registry or version not in registry[name]:
        raise PromptError(f"prompt not registered: {name}@{version}")
    entry = registry[name][version]
    path = repo_root() / entry["path"]
    actual = sha256_file(path)
    if actual != entry["sha256"]:
        raise PromptError(
            f"prompt file hash mismatch for {name}@{version}: file {actual[:12]}…, "
            f"registry {entry['sha256'][:12]}…"
        )
    if expected_sha256 is not None and expected_sha256 != entry["sha256"]:
        raise PromptError(
            f"prompt hash mismatch for {name}@{version}: caller expected "
            f"{expected_sha256[:12]}…, registry has {entry['sha256'][:12]}…"
        )
    return path.read_text(encoding="utf-8")
