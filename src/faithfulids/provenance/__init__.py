"""provenance — L0, the manifest machinery (pure stdlib + jsonschema).

Content hashing, run-ID minting, dirty-worktree refusal, the §6 manifest
writer/verifier, and the immutable STATUS lifecycle. Depends on nothing internal
except ``framework`` types are *not* required here — provenance is deliberately
free of scientific structure so it can manifest any artifact type.
"""

from __future__ import annotations

from faithfulids.provenance.hashing import (
    canonical_json,
    content_address,
    sha256_bytes,
    sha256_file,
    sha256_json,
    sha256_text,
)
from faithfulids.provenance.paths import RepoRootError, repo_root
from faithfulids.provenance.manifest import (
    MANIFEST_SCHEMA,
    SCHEMA_VERSION,
    ArtifactRef,
    Manifest,
    ModelRef,
    OutputFile,
    Status,
    TerminalStatusError,
    canonical_manifest_sha256,
    read_manifest,
    read_status,
    validate_manifest_dict,
    verify_outputs,
    write_manifest,
    write_status,
)
from faithfulids.provenance.run_id import (
    CodeVersion,
    DirtyWorktreeError,
    GitUnavailableError,
    git_commit,
    mint_run_id,
    parse_run_id,
    resolve_code_version,
    utc_stamp,
    worktree_dirty,
)

__all__ = [
    # hashing
    "canonical_json",
    "content_address",
    "sha256_bytes",
    "sha256_file",
    "sha256_json",
    "sha256_text",
    # paths
    "repo_root",
    "RepoRootError",
    # run id / code version
    "CodeVersion",
    "DirtyWorktreeError",
    "GitUnavailableError",
    "git_commit",
    "worktree_dirty",
    "resolve_code_version",
    "mint_run_id",
    "parse_run_id",
    "utc_stamp",
    # manifest
    "Manifest",
    "ArtifactRef",
    "OutputFile",
    "ModelRef",
    "Status",
    "TerminalStatusError",
    "MANIFEST_SCHEMA",
    "SCHEMA_VERSION",
    "write_manifest",
    "read_manifest",
    "validate_manifest_dict",
    "verify_outputs",
    "read_status",
    "write_status",
    "canonical_manifest_sha256",
]
