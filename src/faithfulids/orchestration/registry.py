"""The experiment registry loader (L5).

The registry is append-only and configuration-complete: an experiment exists iff
it has a schema-validated YAML under ``experiments/``. This module loads the
registry, indexes entries by id, and resolves an entry into the flattened form
the runner snapshots into ``config.resolved.yaml`` — verifying every referenced
config, prompt hash, KB version, and seed section along the way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from faithfulids.orchestration.cell_expansion import Cell, expand_cells
from faithfulids.orchestration.config_loader import (
    ConfigError,
    repo_root,
    validate_file,
)
from faithfulids.orchestration.references import (
    collect_prompt_refs,
    resolve_reference,
    verify_prompt,
)


def experiments_root() -> Path:
    return repo_root() / "experiments"


def iter_experiment_files() -> list[Path]:
    return sorted(experiments_root().rglob("*.yaml"))


@lru_cache(maxsize=1)
def load_all_experiments() -> dict[str, dict[str, Any]]:
    """Index every registered experiment by id (schema-validated)."""
    index: dict[str, dict[str, Any]] = {}
    for path in iter_experiment_files():
        cfg = validate_file(path)
        exp_id = cfg["id"]
        if exp_id in index:
            raise ConfigError(
                f"duplicate experiment id {exp_id!r} in {path} — the registry is "
                "append-only; use a new id with supersedes:"
            )
        index[exp_id] = cfg
    return index


def load_experiment(experiment_id: str) -> dict[str, Any]:
    index = load_all_experiments()
    if experiment_id not in index:
        raise ConfigError(f"experiment not registered: {experiment_id!r}")
    return index[experiment_id]


@dataclass
class ResolvedExperiment:
    """The flattened, fully-verified form of an experiment (basis of the snapshot)."""

    experiment_id: str
    experiment: dict[str, Any]
    cells: list[Cell]
    resolved_configs: dict[str, Any] = field(default_factory=dict)
    seeds: dict[str, Any] = field(default_factory=dict)
    verified_prompt_hashes: list[str] = field(default_factory=list)

    @property
    def n_cells(self) -> int:
        return len(self.cells)


def _load_config_ref(ref: str, resolved: dict[str, Any], prompts: list[str]) -> None:
    cfg = resolve_reference(ref)
    if isinstance(cfg, dict) and cfg.get("kind"):
        resolved[ref] = cfg
        for pr in collect_prompt_refs(cfg):
            prompts.append(verify_prompt(pr))


def resolve_experiment(experiment_id: str) -> ResolvedExperiment:
    """Verify and flatten an experiment into its resolved form.

    Loads and validates every referenced config, verifies every prompt hash and
    KB version, resolves the seed section, and expands the cells. Fails loudly on
    any dangling reference or instrument drift.
    """
    exp = load_experiment(experiment_id)
    resolved: dict[str, Any] = {}
    prompts: list[str] = []

    design = exp["design"]
    if design["mode"] == "factorial":
        axes = design["axes"]
        for dataset in axes["datasets"]:
            _load_config_ref(f"datasets:{dataset}", resolved, prompts)
        for detector in axes["detectors"]:
            det = resolve_reference(f"detectors:{detector}")
            resolved[f"detectors:{detector}"] = det
            _load_config_ref(det["attribution_ref"], resolved, prompts)
        for llm in axes["llms"]:
            _load_config_ref(f"llms:{llm}", resolved, prompts)
        for generator in axes["generators"]:
            _load_config_ref(f"generators:{generator}", resolved, prompts)

    for ref in exp.get("sampling_refs", []):
        resolved[ref] = resolve_reference(ref)
    for ref in exp.get("metric_refs", []):
        _load_config_ref(ref, resolved, prompts)
    for value in exp.get("config_refs", {}).values():
        if isinstance(value, str) and ":" in value and not value.endswith(".md"):
            try:
                _load_config_ref(value, resolved, prompts)
            except ConfigError:
                # non-config path references (e.g. materials_build dirs) are left as-is
                pass

    seeds: dict[str, Any] = {}
    if exp.get("seed_ref"):
        seeds = resolve_reference(exp["seed_ref"])

    cells = expand_cells(exp)
    return ResolvedExperiment(
        experiment_id=experiment_id,
        experiment=exp,
        cells=cells,
        resolved_configs=resolved,
        seeds=seeds,
        verified_prompt_hashes=sorted(set(prompts)),
    )
