"""Run-ID minting, parsing, and the dirty-worktree refusal."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

import pytest

from faithfulids.provenance import (
    CodeVersion,
    DirtyWorktreeError,
    mint_run_id,
    parse_run_id,
    resolve_code_version,
    utc_stamp,
)


def test_utc_stamp_format():
    ts = utc_stamp(datetime(2026, 8, 12, 9, 30, tzinfo=timezone.utc))
    assert ts == "2026-08-12T0930Z"


def test_mint_and_parse_run_id():
    cv = CodeVersion(git_commit="a1b2c3d4e5f6", dirty=False)
    rid = mint_run_id(
        "EXP-A-001", cv, now=datetime(2026, 8, 12, 9, 30, tzinfo=timezone.utc)
    )
    assert rid == "EXP-A-001__a1b2c3d__2026-08-12T0930Z"
    parts = parse_run_id(rid)
    assert parts["exp"] == "EXP-A-001"
    assert parts["sha"] == "a1b2c3d"
    assert parts["utc"] == "2026-08-12T0930Z"


def test_parse_rejects_malformed():
    with pytest.raises(ValueError):
        parse_run_id("not-a-run-id")


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture()
def temp_repo(tmp_path):
    _git(["init"], tmp_path)
    _git(["config", "user.email", "t@example.com"], tmp_path)
    _git(["config", "user.name", "t"], tmp_path)
    (tmp_path / "a.txt").write_text("one", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-m", "init"], tmp_path)
    return tmp_path


def test_clean_worktree_is_citable(temp_repo):
    cv = resolve_code_version(temp_repo)
    assert cv.dirty is False
    assert cv.citable is True
    assert len(cv.git_commit) == 40


def test_dirty_worktree_refused_by_default(temp_repo):
    (temp_repo / "a.txt").write_text("two", encoding="utf-8")
    with pytest.raises(DirtyWorktreeError):
        resolve_code_version(temp_repo)


def test_dirty_worktree_allowed_in_debug_is_noncitable(temp_repo):
    (temp_repo / "a.txt").write_text("two", encoding="utf-8")
    cv = resolve_code_version(temp_repo, allow_dirty=True)
    assert cv.dirty is True
    assert cv.citable is False
