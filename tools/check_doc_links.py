#!/usr/bin/env python3
"""Verify that intra-repository markdown links resolve (backs `docs-build.yml`).

Scans every tracked ``*.md`` file, extracts inline links of the form
``[text](target)``, skips external/anchor/mailto links, and fails if a local
target does not exist. Link targets may carry a ``:line`` suffix or an ``#anchor``
fragment, both of which are stripped before resolution.

Pure standard library; runs in the docs-build CI job without the science stack.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:")
# Directories we do not walk (payloads / caches / vcs).
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def _iter_markdown(root: Path):
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _resolve(md_file: Path, target: str) -> bool:
    # strip fragment and optional :line suffix
    target = target.split("#", 1)[0]
    target = re.sub(r":\d+$", "", target)
    if target == "":
        return True  # pure in-page anchor
    candidate = (md_file.parent / target).resolve()
    return candidate.exists()


def main() -> int:
    broken: list[str] = []
    checked = 0
    for md in _iter_markdown(REPO_ROOT):
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in LINK_RE.finditer(text):
            target = m.group(1).strip()
            if target.startswith(SKIP_PREFIXES):
                continue
            checked += 1
            if not _resolve(md, target):
                rel = md.relative_to(REPO_ROOT)
                broken.append(f"{rel}: broken link -> {target}")
    if broken:
        print("Broken intra-repo markdown links:", file=sys.stderr)
        for b in broken:
            print("  " + b, file=sys.stderr)
        return 1
    print(f"OK: {checked} local markdown links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
