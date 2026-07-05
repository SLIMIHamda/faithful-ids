"""Config loading + JSON-Schema validation (L5).

Maps every config/experiment/KB file to its family schema in ``configs/schema/``
(or ``kb/schema/``) and validates it. A missing required key is a hard error —
there are no silent defaults. Uses only ``pyyaml`` + ``jsonschema`` so the
``validate-configs`` CI job need not install the scientific stack.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import jsonschema
import yaml

from faithfulids.provenance import repo_root  # layer-safe repo-root discovery (L0)


class ConfigError(RuntimeError):
    """Raised on any config-system failure (missing key, bad ref, hash miss)."""


# Directory (relative to configs/) -> config family / schema stem.
_FAMILY_BY_DIR = {
    "datasets": "dataset",
    "detectors": "detector",
    "attribution": "attribution",
    "llms": "llm",
    "generators": "generator",
    "extraction": "extraction",
    "corruption": "corruption",
    "metrics": "metric",
    "sampling": "sampling",
    "seeds": "seed_table",
}


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top-level YAML must be a mapping")
    return data


@lru_cache(maxsize=64)
def load_schema(stem: str) -> dict[str, Any]:
    """Load a JSON Schema by stem, e.g. ``dataset`` -> ``configs/schema/dataset.v1.json``."""
    if stem == "kb":
        path = repo_root() / "kb" / "schema" / "kb.v1.json"
    else:
        path = repo_root() / "configs" / "schema" / f"{stem}.v1.json"
    if not path.is_file():
        raise ConfigError(f"schema not found for stem {stem!r}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_stem_for(path: Path) -> str:
    """Determine which schema validates ``path`` from its location."""
    root = repo_root()
    rel = path.resolve().relative_to(root)
    parts = rel.parts
    if parts[0] == "configs":
        family_dir = parts[1]
        if family_dir == "statistics":
            # one schema per statistics file (frozen prereg tree)
            return path.stem  # hypothesis_families | decision_thresholds | tests
        stem = _FAMILY_BY_DIR.get(family_dir)
        if stem is None:
            raise ConfigError(f"no schema mapping for configs/{family_dir}/")
        return stem
    if parts[0] == "experiments":
        return "experiment"
    if parts[0] == "kb" and parts[1] in ("feature_semantics", "attack_classes"):
        return "kb"
    raise ConfigError(f"cannot classify config file: {rel}")


def validate_file(path: str | Path) -> dict[str, Any]:
    """Load a config file and validate it against its family schema."""
    path = Path(path)
    data = load_yaml(path)
    stem = _schema_stem_for(path)
    schema = load_schema(stem)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        raise ConfigError(f"{path}: schema violation: {exc.message}") from exc
    return data


def iter_config_files() -> Iterator[Path]:
    """Every schema-validatable config/experiment/KB file in the repo."""
    root = repo_root()
    configs = root / "configs"
    for p in sorted(configs.rglob("*.yaml")):
        if "schema" in p.parts:
            continue
        yield p
    for p in sorted((root / "experiments").rglob("*.yaml")):
        yield p
    for sub in ("feature_semantics", "attack_classes"):
        for p in sorted((root / "kb" / sub).rglob("*.yaml")):
            yield p


def config_dir(family: str) -> Path:
    """The directory holding configs of ``family`` (singular family name)."""
    inverse = {v: k for k, v in _FAMILY_BY_DIR.items()}
    if family == "statistics":
        return repo_root() / "configs" / "statistics"
    sub = inverse.get(family)
    if sub is None:
        raise ConfigError(f"unknown config family: {family!r}")
    return repo_root() / "configs" / sub


def load_config(family: str, config_id: str) -> dict[str, Any]:
    """Load a single config by family + id (validated)."""
    path = config_dir(family) / f"{config_id}.yaml"
    if not path.is_file():
        raise ConfigError(f"config not found: {family}:{config_id} ({path})")
    return validate_file(path)
