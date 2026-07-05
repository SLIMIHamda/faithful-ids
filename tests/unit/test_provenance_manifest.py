"""Manifest build/validate/write/read, output verification, STATUS lifecycle."""

from __future__ import annotations

import jsonschema
import pytest

from faithfulids.provenance import (
    ArtifactRef,
    CodeVersion,
    Manifest,
    ModelRef,
    OutputFile,
    Status,
    TerminalStatusError,
    read_manifest,
    read_status,
    sha256_file,
    verify_outputs,
    write_manifest,
    write_status,
)


def _manifest(**overrides) -> Manifest:
    base = dict(
        artifact_id="EXP-TOY-001__abc1234__2026-08-12T0930Z",
        artifact_type="run",
        pipeline_stage="metrics",
        code_version=CodeVersion("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2", dirty=False),
        resolved_config_sha256="a" * 64,
        environment={"environment_hash": "e" * 64},
        start_utc="2026-08-12T09:30:00Z",
        status=Status.RUNNING,
        experiment_id="EXP-TOY-001",
        inputs=[ArtifactRef("split:toy", "b" * 64, kind="split")],
        randomness={"generation/cell0": 42},
        models=[ModelRef("detector", "xgboost@sha", None, None)],
    )
    base.update(overrides)
    return Manifest(**base)


def test_manifest_validates_against_schema():
    _manifest().validate()  # raises if non-conforming


def test_manifest_write_read_roundtrip(tmp_path):
    m = _manifest()
    write_manifest(tmp_path, m)
    back = read_manifest(tmp_path)
    assert back.to_dict() == m.to_dict()


def test_verify_outputs_detects_missing_and_mismatch(tmp_path):
    # create a real output file and reference it truthfully
    out = tmp_path / "artifacts" / "metrics.parquet"
    out.parent.mkdir(parents=True)
    out.write_bytes(b"metric-bytes")
    good = OutputFile(path="artifacts/metrics.parquet", sha256=sha256_file(out))
    m = _manifest(status=Status.COMPLETE, end_utc="2026-08-12T09:31:00Z", outputs=[good])
    write_manifest(tmp_path, m)
    assert verify_outputs(tmp_path) == []

    # tamper with the payload -> hash mismatch detected
    out.write_bytes(b"tampered")
    problems = verify_outputs(tmp_path)
    assert len(problems) == 1 and "hash mismatch" in problems[0]


def test_manifest_rejects_absolute_and_drive_letter_paths():
    with pytest.raises(jsonschema.ValidationError):
        _manifest(outputs=[OutputFile(path="C:/x/metrics.parquet", sha256="a" * 64)]).validate()
    with pytest.raises(jsonschema.ValidationError):
        _manifest(outputs=[OutputFile(path="/abs/metrics.parquet", sha256="a" * 64)]).validate()


def test_status_terminal_is_immutable(tmp_path):
    write_status(tmp_path, Status.RUNNING)
    assert read_status(tmp_path) is Status.RUNNING
    write_status(tmp_path, Status.COMPLETE)
    assert read_status(tmp_path) is Status.COMPLETE
    with pytest.raises(TerminalStatusError):
        write_status(tmp_path, Status.FAILED)
    with pytest.raises(TerminalStatusError):
        write_status(tmp_path, Status.RUNNING)
