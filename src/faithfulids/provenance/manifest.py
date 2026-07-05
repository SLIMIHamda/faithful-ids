"""Manifest writer / verifier and the STATUS lifecycle (L0).

Implements the blueprint §6 manifest: a typed model that serialises to a
document conforming to :data:`MANIFEST_SCHEMA` (``manifest.v1.json``), plus the
verification and status-transition primitives the write-once run ledger is built
on. Terminal statuses (``COMPLETE`` / ``FAILED``) are immutable.

Uses ``jsonschema`` (a pinned, hard dependency) for validation; otherwise pure
standard library.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from faithfulids.provenance.hashing import canonical_json, sha256_file
from faithfulids.provenance.run_id import CodeVersion

_SCHEMA_PATH = Path(__file__).with_name("manifest.v1.json")
MANIFEST_SCHEMA: dict[str, Any] = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
SCHEMA_VERSION = "v1"
MANIFEST_FILENAME = "MANIFEST.json"
STATUS_FILENAME = "STATUS"


class Status(enum.Enum):
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

    @property
    def terminal(self) -> bool:
        return self in (Status.COMPLETE, Status.FAILED)


@dataclass(frozen=True)
class ArtifactRef:
    """One entry of a manifest's ``inputs`` — an (id, hash) pair."""

    artifact_id: str
    content_sha256: str
    kind: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "content_sha256": self.content_sha256,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class OutputFile:
    path: str
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class ModelRef:
    role: str  # detector | llm | extractor | judge | imputation
    identity: str
    quantisation: str | None = None
    revision: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "identity": self.identity,
            "quantisation": self.quantisation,
            "revision": self.revision,
        }


@dataclass
class Manifest:
    """A typed §6 manifest for any artifact directory."""

    artifact_id: str
    artifact_type: str  # dataset|model|cache|run|analysis_output|figure|table
    pipeline_stage: str
    code_version: CodeVersion
    resolved_config_sha256: str
    environment: dict[str, Any]
    start_utc: str
    status: Status
    experiment_id: str | None = None
    resolved_config_path: str | None = None
    inputs: list[ArtifactRef] = field(default_factory=list)
    randomness: dict[str, int] = field(default_factory=dict)
    models: list[ModelRef] = field(default_factory=list)
    end_utc: str | None = None
    outputs: list[OutputFile] = field(default_factory=list)
    gate: str | None = None

    # -- serialisation ------------------------------------------------------ #
    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": {
                "artifact_id": self.artifact_id,
                "artifact_type": self.artifact_type,
                "schema_version": SCHEMA_VERSION,
            },
            "producer": {
                "experiment_id": self.experiment_id,
                "pipeline_stage": self.pipeline_stage,
                "code_version": {
                    "git_commit": self.code_version.git_commit,
                    "dirty": self.code_version.dirty,
                    "citable": self.code_version.citable,
                },
            },
            "configuration": {
                "resolved_config_sha256": self.resolved_config_sha256,
                "resolved_config_path": self.resolved_config_path,
            },
            "inputs": [i.to_dict() for i in self.inputs],
            "environment": self.environment,
            "randomness": dict(self.randomness),
            "models": [m.to_dict() for m in self.models],
            "timestamps": {"start_utc": self.start_utc, "end_utc": self.end_utc},
            "outputs": [o.to_dict() for o in self.outputs],
            "status": self.status.value,
            "gate": self.gate,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Manifest":
        cv = d["producer"]["code_version"]
        return cls(
            artifact_id=d["identity"]["artifact_id"],
            artifact_type=d["identity"]["artifact_type"],
            pipeline_stage=d["producer"]["pipeline_stage"],
            code_version=CodeVersion(
                git_commit=cv["git_commit"], dirty=bool(cv["dirty"])
            ),
            resolved_config_sha256=d["configuration"]["resolved_config_sha256"],
            environment=d["environment"],
            start_utc=d["timestamps"]["start_utc"],
            status=Status(d["status"]),
            experiment_id=d["producer"].get("experiment_id"),
            resolved_config_path=d["configuration"].get("resolved_config_path"),
            inputs=[ArtifactRef(**i) for i in d.get("inputs", [])],
            randomness=dict(d.get("randomness", {})),
            models=[ModelRef(**m) for m in d.get("models", [])],
            end_utc=d["timestamps"].get("end_utc"),
            outputs=[OutputFile(**o) for o in d.get("outputs", [])],
            gate=d.get("gate"),
        )

    # -- validation --------------------------------------------------------- #
    def validate(self) -> None:
        """Raise ``jsonschema.ValidationError`` if not schema-conforming."""
        jsonschema.validate(instance=self.to_dict(), schema=MANIFEST_SCHEMA)


def validate_manifest_dict(d: dict[str, Any]) -> None:
    jsonschema.validate(instance=d, schema=MANIFEST_SCHEMA)


# --------------------------------------------------------------------------- #
# Directory I/O
# --------------------------------------------------------------------------- #
def write_manifest(artifact_dir: str | Path, manifest: Manifest) -> Path:
    """Validate then write ``MANIFEST.json`` into ``artifact_dir``."""
    manifest.validate()
    d = Path(artifact_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / MANIFEST_FILENAME
    path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def read_manifest(artifact_dir: str | Path) -> Manifest:
    path = Path(artifact_dir) / MANIFEST_FILENAME
    d = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest_dict(d)
    return Manifest.from_dict(d)


def verify_outputs(artifact_dir: str | Path) -> list[str]:
    """Recompute every listed output's sha256; return a list of problems.

    An empty list means every declared output exists and hash-matches — the
    integrity check behind ``manifest-audit.yml`` (hostile-audit A6).
    """
    d = Path(artifact_dir)
    manifest = read_manifest(d)
    problems: list[str] = []
    for out in manifest.outputs:
        fp = d / out.path
        if not fp.is_file():
            problems.append(f"missing output: {out.path}")
            continue
        actual = sha256_file(fp)
        if actual != out.sha256:
            problems.append(
                f"hash mismatch: {out.path} (manifest {out.sha256[:12]}…, "
                f"actual {actual[:12]}…)"
            )
    return problems


# --------------------------------------------------------------------------- #
# STATUS lifecycle — terminal states are immutable
# --------------------------------------------------------------------------- #
class TerminalStatusError(RuntimeError):
    """Raised on any attempt to overwrite a terminal STATUS."""


def read_status(run_dir: str | Path) -> Status | None:
    path = Path(run_dir) / STATUS_FILENAME
    if not path.is_file():
        return None
    return Status(path.read_text(encoding="utf-8").strip())


def write_status(run_dir: str | Path, status: Status) -> None:
    """Write STATUS, refusing to overwrite an existing terminal status.

    RUNNING → COMPLETE and RUNNING → FAILED are allowed; COMPLETE/FAILED are
    immutable. This is the filesystem half of "runs/ is write-once"; the
    orchestration layer additionally refuses to reopen a run directory.
    """
    d = Path(run_dir)
    d.mkdir(parents=True, exist_ok=True)
    current = read_status(d)
    if current is not None and current.terminal:
        raise TerminalStatusError(
            f"STATUS is already terminal ({current.value}) — runs/ is write-once; "
            "re-execution mints a new run id."
        )
    (d / STATUS_FILENAME).write_text(status.value + "\n", encoding="utf-8")


def canonical_manifest_sha256(manifest: Manifest) -> str:
    """sha256 of the manifest's canonical JSON (for lineage/audit chaining)."""
    from faithfulids.provenance.hashing import sha256_text

    return sha256_text(canonical_json(manifest.to_dict()))
