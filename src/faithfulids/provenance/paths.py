"""Repository-root discovery (L0).

A single, layer-safe way for any layer to locate the repository root (the dir
holding ``configs/schema`` and ``pyproject.toml``). Kept in ``provenance`` (L0)
so that L2 (``llm`` prompt loading) and L5 (``orchestration`` config loading) can
both use it without importing across layers. Pure standard library.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


class RepoRootError(RuntimeError):
    """Raised when the repository root cannot be located."""


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """Locate the repository root.

    Honours ``$FAITHFULIDS_REPO_ROOT`` if set; otherwise searches upward from
    this file, then from the current working directory, for the marker
    ``configs/schema``.
    """
    env = os.environ.get("FAITHFULIDS_REPO_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for cand in here.parents:
        if (cand / "configs" / "schema").is_dir() and (cand / "pyproject.toml").is_file():
            return cand
    for cand in [Path.cwd(), *Path.cwd().parents]:
        if (cand / "configs" / "schema").is_dir():
            return cand
    raise RepoRootError("could not locate repo root (configs/schema not found)")
