#!/usr/bin/env python3
"""Diff the pre-registered statistics tree against tag prereg-v1 (CI job
`prereg-freeze`).

The frozen files (``configs/statistics/*.yaml``) must be unchanged since the tag;
changes only arrive as append-only files under ``configs/statistics/amendments/``
(hostile-audit A5). Before the tag exists (pre-registration not yet performed)
there is nothing to freeze — the check passes with a note.

Run: ``python tools/prereg_diff.py [--require-tag]``
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TAG = "prereg-v1"
FROZEN = ["hypothesis_families.yaml", "decision_thresholds.yaml", "tests.yaml"]


def _git(args: list[str]) -> tuple[int, str]:
    # encoding pinned: the frozen files are UTF-8 (ε in hypothesis text); the
    # locale default (cp1252 on Windows) would mangle `git show` output.
    p = subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True, encoding="utf-8"
    )
    return p.returncode, p.stdout.strip()


def tag_exists() -> bool:
    code, _ = _git(["rev-parse", "-q", "--verify", f"refs/tags/{TAG}"])
    return code == 0


def _normalized(text: str) -> str:
    # `_git` strips stdout and subprocess text-mode translates newlines, so the
    # tag side arrives LF-only without a trailing newline; give the working-tree
    # side the identical treatment or every file compares unequal.
    return text.replace("\r\n", "\n").strip()


def diff() -> list[str]:
    changed: list[str] = []
    for name in FROZEN:
        rel = f"configs/statistics/{name}"
        code, at_tag = _git(["show", f"{TAG}:{rel}"])
        if code != 0:
            changed.append(f"{rel}: absent at tag {TAG}")
            continue
        now = (REPO / rel).read_text(encoding="utf-8")
        if _normalized(now) != _normalized(at_tag):
            changed.append(f"{rel}: changed since {TAG} (use an append-only amendment)")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-tag", action="store_true")
    args = parser.parse_args()

    if not tag_exists():
        msg = f"prereg-freeze: tag {TAG} not set yet — nothing to freeze (pre-registration pending)."
        if args.require_tag:
            print(msg)
        else:
            print(msg)
        return 0

    changed = diff()
    if changed:
        print("prereg-freeze: FAILED — pre-registered files changed since tag:", file=sys.stderr)
        for c in changed:
            print(f"  - {c}", file=sys.stderr)
        return 1
    print(f"prereg-freeze: OK — pre-registered statistics unchanged since {TAG}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
