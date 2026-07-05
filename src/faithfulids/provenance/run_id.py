"""Run-ID minting and the dirty-worktree refusal (L0).

A run is stamped with the exact code that produced it: the git commit and
whether the worktree was dirty. **Dirty runs are refused** by the runner, except
in an explicit debug mode that marks their outputs ``NON-CITABLE`` (immutable
constraint #6). Run IDs embed the commit and the UTC start time so they are
unique, self-dating, and never reused (naming convention in
``docs/naming-conventions.md``).

Pure standard library (``subprocess`` to shell out to ``git``).
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class DirtyWorktreeError(RuntimeError):
    """Raised when a run is attempted on a dirty worktree outside debug mode."""


class GitUnavailableError(RuntimeError):
    """Raised when git metadata cannot be obtained (no repo / git missing)."""


@dataclass(frozen=True)
class CodeVersion:
    """The code identity recorded in a manifest's ``producer.code_version``."""

    git_commit: str
    dirty: bool

    @property
    def short(self) -> str:
        return self.git_commit[:7]

    @property
    def citable(self) -> bool:
        """A dirty worktree is never citable; a clean commit is."""
        return not self.dirty


def _git(args: list[str], repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(repo),
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:  # git not installed
        raise GitUnavailableError("git executable not found") from exc
    except subprocess.CalledProcessError as exc:
        raise GitUnavailableError(
            f"git {' '.join(args)} failed: {exc.stderr.strip()}"
        ) from exc
    return out.stdout.strip()


def git_commit(repo: str | Path = ".") -> str:
    """Full 40-char commit sha of HEAD."""
    return _git(["rev-parse", "HEAD"], Path(repo))


def worktree_dirty(repo: str | Path = ".") -> bool:
    """True if there are staged or unstaged changes (tracked or untracked)."""
    status = _git(["status", "--porcelain"], Path(repo))
    return status != ""


def resolve_code_version(
    repo: str | Path = ".", *, allow_dirty: bool = False
) -> CodeVersion:
    """Resolve the current code version, refusing a dirty worktree by default.

    ``allow_dirty=True`` is the explicit debug mode: it returns a
    ``CodeVersion`` with ``dirty=True`` (hence ``citable=False``) so the runner
    can stamp outputs ``NON-CITABLE`` rather than aborting.
    """
    repo = Path(repo)
    commit = git_commit(repo)
    dirty = worktree_dirty(repo)
    if dirty and not allow_dirty:
        raise DirtyWorktreeError(
            "Refusing to run on a dirty worktree. Commit your changes, or run in "
            "debug mode (allow_dirty=True) — debug outputs are stamped NON-CITABLE "
            "and may never back a paper number."
        )
    return CodeVersion(git_commit=commit, dirty=dirty)


_UTC_FMT = "%Y-%m-%dT%H%MZ"
_RUN_ID_RE = re.compile(
    r"^(?P<exp>[A-Za-z0-9._-]+)__(?P<sha>[0-9a-f]{7})__(?P<utc>\d{4}-\d{2}-\d{2}T\d{4}Z)$"
)


def utc_stamp(now: datetime | None = None) -> str:
    """Compact UTC timestamp used in run/analysis IDs (e.g. 2026-08-12T0930Z)."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return now.strftime(_UTC_FMT)


def mint_run_id(
    experiment_id: str, code_version: CodeVersion, now: datetime | None = None
) -> str:
    """``<EXP-ID>__<git-sha7>__<UTC>`` — unique, self-dating, never reused."""
    if not experiment_id:
        raise ValueError("experiment_id must be non-empty")
    return f"{experiment_id}__{code_version.short}__{utc_stamp(now)}"


def parse_run_id(run_id: str) -> dict[str, str]:
    """Inverse of :func:`mint_run_id` (for auditing/lineage)."""
    m = _RUN_ID_RE.match(run_id)
    if not m:
        raise ValueError(f"malformed run id: {run_id!r}")
    return m.groupdict()
