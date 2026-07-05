"""Reference resolution (L5).

Configs reference other configs, prompts by hash, the KB by version, and seeds
by table section. This module turns those references into resolved values and,
crucially, **fails loudly** if a referenced prompt hash or KB version does not
match its registry — a drifted instrument can never be silently substituted
(blueprint §6).

Reference grammar (strings):
    <family>:<id>                         e.g. sampling:n400_stratified
    seeds:<section>                       e.g. seeds:tier_a          -> section dict
    statistics:<file>:<key>               e.g. statistics:decision_thresholds:verifier_threshold
    kb:<name>@<version>                   e.g. kb:cicids2017@1.0.0
Prompt references are objects {name, version, sha256}.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from faithfulids.orchestration.config_loader import (
    ConfigError,
    load_config,
    repo_root,
)
from faithfulids.provenance.hashing import sha256_file

_FAMILY_REF = re.compile(r"^(?P<family>[a-z_]+):(?P<rest>.+)$")
_KB_REF = re.compile(r"^kb:(?P<name>[a-z0-9_]+)@(?P<version>[0-9]+\.[0-9]+\.[0-9]+)$")

# family token in a ref -> config family (singular) used by load_config
_REF_FAMILY = {
    "datasets": "dataset",
    "detectors": "detector",
    "attribution": "attribution",
    "llms": "llm",
    "generators": "generator",
    "extraction": "extraction",
    "corruption": "corruption",
    "metrics": "metric",
    "sampling": "sampling",
}


@lru_cache(maxsize=1)
def _prompt_registry() -> dict[str, Any]:
    path = repo_root() / "prompts" / "REGISTRY.json"
    return json.loads(path.read_text(encoding="utf-8"))["prompts"]


@lru_cache(maxsize=1)
def _kb_versions() -> dict[str, str]:
    path = repo_root() / "kb" / "VERSIONS.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["names"]


@lru_cache(maxsize=1)
def _seed_table() -> dict[str, Any]:
    return load_config("seed_table", "seed_table")["sections"]


def resolve_reference(ref: str) -> Any:
    """Resolve a string reference to its target value (fails loudly)."""
    if ref.startswith("kb:"):
        return resolve_kb(ref)
    m = _FAMILY_REF.match(ref)
    if not m:
        raise ConfigError(f"malformed reference: {ref!r}")
    family, rest = m.group("family"), m.group("rest")
    if family == "seeds":
        section = _seed_table().get(rest)
        if section is None:
            raise ConfigError(f"seed section not found: {rest!r} (ref {ref})")
        return section
    if family == "statistics":
        return _resolve_statistics(rest, ref)
    conf_family = _REF_FAMILY.get(family)
    if conf_family is None:
        raise ConfigError(f"unknown reference family: {family!r} (ref {ref})")
    return load_config(conf_family, rest)


def _resolve_statistics(rest: str, ref: str) -> Any:
    parts = rest.split(":")
    file_stem = parts[0]  # decision_thresholds | hypothesis_families | tests
    path = repo_root() / "configs" / "statistics" / f"{file_stem}.yaml"
    if not path.is_file():
        raise ConfigError(f"statistics config not found: {file_stem} (ref {ref})")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if len(parts) == 1:
        return data
    if file_stem == "decision_thresholds":
        key = parts[1]
        thresholds = data["thresholds"]
        if key not in thresholds:
            raise ConfigError(f"threshold not found: {key!r} (ref {ref})")
        return thresholds[key]
    raise ConfigError(f"unsupported statistics reference: {ref!r}")


def resolve_kb(ref: str) -> dict[str, str]:
    """Validate a ``kb:<name>@<version>`` ref against ``kb/VERSIONS.yaml``."""
    m = _KB_REF.match(ref)
    if not m:
        raise ConfigError(f"malformed KB reference: {ref!r}")
    name, version = m.group("name"), m.group("version")
    known = _kb_versions()
    if name not in known:
        raise ConfigError(f"unknown KB name: {name!r} (ref {ref})")
    if known[name] != version:
        raise ConfigError(
            f"KB version drift: {name} pinned at {version} but registry has "
            f"{known[name]} (ref {ref})"
        )
    return {"name": name, "version": version}


def verify_prompt(prompt: dict[str, Any]) -> str:
    """Verify a prompt reference {name, version, sha256} against registry + file.

    Returns the verified sha256. Raises if the registry, the config, and the file
    on disk do not all agree — the mechanism that makes a prompt a frozen,
    hash-addressed instrument.
    """
    name, version, declared = prompt["name"], prompt["version"], prompt["sha256"]
    registry = _prompt_registry()
    if name not in registry or version not in registry[name]:
        raise ConfigError(f"prompt not registered: {name}@{version}")
    entry = registry[name][version]
    if entry["sha256"] != declared:
        raise ConfigError(
            f"prompt hash mismatch for {name}@{version}: config says {declared[:12]}…, "
            f"registry says {entry['sha256'][:12]}…"
        )
    file_hash = sha256_file(repo_root() / entry["path"])
    if file_hash != declared:
        raise ConfigError(
            f"prompt file hash mismatch for {name}@{version}: file is {file_hash[:12]}…, "
            f"declared {declared[:12]}… — the frozen instrument changed on disk"
        )
    return declared


def collect_prompt_refs(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Find every prompt reference embedded in a config (generator/extraction/metric)."""
    refs: list[dict[str, Any]] = []
    if config.get("kind") == "generator":
        if config.get("prompt"):
            refs.append(config["prompt"])
        verifier = config.get("verifier")
        if verifier and verifier.get("prompt"):
            refs.append(verifier["prompt"])
    elif config.get("kind") == "extraction":
        refs.append(config["prompt"])
    elif config.get("kind") == "metric" and config.get("judge", {}).get("prompt"):
        refs.append(config["judge"]["prompt"])
    return refs
