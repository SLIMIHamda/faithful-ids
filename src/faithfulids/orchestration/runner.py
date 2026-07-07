"""The stage runner (L5).

Executes the per-cell stage sequence — *attribution → generation → extraction →
metrics* — and writes an immutable, hash-manifested run directory. Metric rows
are computed generator-blind (the metric callables never receive generator
identity) and the grouping key is attached *afterwards*, here in orchestration.

The write-once contract is enforced two ways: the run directory is opened fresh
(refusing to reopen an existing one) and terminal STATUS is immutable
(``provenance``). Nothing under ``runs/`` is ever modified.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import yaml

from faithfulids.framework import (
    AttributionArtifact,
    ClaimExtractor,
    ClaimSet,
    DetectorArtifact,
    ExplanationRecord,
    GenerationContext,
    Generator,
)
from faithfulids.metrics.layer1 import compute_all as layer1_all
from faithfulids.metrics.layer2 import compute_all as layer2_all
from faithfulids.metrics.layer2 import compute_eps_model as layer2_eps_model
from faithfulids.metrics.layer2 import SimpleBackgroundErasure
from faithfulids.provenance import (
    ArtifactRef,
    CodeVersion,
    Manifest,
    ModelRef,
    OutputFile,
    Status,
    sha256_file,
    sha256_json,
    write_manifest,
    write_status,
)


class RunDirectoryExists(RuntimeError):
    """Raised when a run directory already exists (runs/ is write-once)."""


@dataclass
class InstanceCase:
    """One explained instance: its features, attribution, and detector output."""

    instance_id: str
    feature_values: dict[str, float]
    attribution: AttributionArtifact
    detector_prediction: float
    predicted_class: str


@dataclass
class Components:
    """The resolved, injected components for a run (generator-agnostic parts)."""

    detector: DetectorArtifact
    extractor: ClaimExtractor
    erasure: Any  # ErasureOperator
    dataset_id: str
    layer1_top_k: int
    layer2_k_values: Sequence[int]


@dataclass
class CellArtifacts:
    explanations: list[ExplanationRecord] = field(default_factory=list)
    claims: list[ClaimSet] = field(default_factory=list)
    metric_rows: list[dict[str, Any]] = field(default_factory=list)


def run_cells(
    cases: Sequence[InstanceCase],
    generators: Sequence[tuple[str, Generator]],
    components: Components,
    *,
    seed: int,
) -> CellArtifacts:
    """Run generation → extraction → metrics for every (instance, generator).

    Layer-2 ε_att (attribution-driven) is model-level and emitted once per
    instance; Layer-2 ε_model (claim-driven) and Layer-1 are per (instance,
    generator). In every case the metric functions are called WITHOUT generator
    identity — ε_model receives the claim set, not the generator id; the grouping
    key is attached to the row afterwards (ADR-0001).
    """
    art = CellArtifacts()

    # Layer-2 ε_att (attribution-driven, claim-free): generator-blind, once per
    # instance — probes whether φ picks the features the model uses (φ ↔ f).
    for case in cases:
        for k in components.layer2_k_values:
            l2 = layer2_all(case.attribution, components.detector, case.feature_values,
                            components.erasure, k=k)
            for name, value in l2.items():
                art.metric_rows.append({
                    "instance_id": case.instance_id, "layer": "layer2", "metric": name,
                    "k": k, "value": value, "component": "eps_att",
                    "grouping": {"instance_id": case.instance_id},  # NO generator identity
                })

    # Generation → extraction → Layer-1 per (instance, generator).
    total = len(generators) * len(cases)
    done = 0
    for gen_id, generator in generators:
        for case in cases:
            ctx = GenerationContext(
                instance_id=case.instance_id,
                feature_values=case.feature_values,
                attribution=case.attribution,
                detector_prediction=case.detector_prediction,
                predicted_class=case.predicted_class,
                dataset_id=components.dataset_id,
                metadata={"seed": seed},
            )
            record = generator.generate(ctx)
            claimset = components.extractor.extract(record)
            art.explanations.append(record)
            art.claims.append(claimset)
            l1 = layer1_all(claimset, case.attribution, top_k=components.layer1_top_k)
            for name, value in l1.items():
                art.metric_rows.append({
                    "instance_id": case.instance_id, "layer": "layer1", "metric": name,
                    "value": value,
                    # grouping (generator identity) attached HERE, post-computation
                    "grouping": {"instance_id": case.instance_id, "generator_id": gen_id},
                })
            # Layer-2 ε_model (claim-driven): erase the CITED features S. Claim
            # *content* is a legal metric input; generator *identity* is never
            # passed to the metric — it is attached below only as an opaque
            # grouping key, exactly as for Layer-1 (ADR-0001).
            for k in components.layer2_k_values:
                em = layer2_eps_model(claimset, components.detector, case.feature_values,
                                      components.erasure, k=k)
                for name, value in em.items():
                    art.metric_rows.append({
                        "instance_id": case.instance_id, "layer": "layer2", "metric": name,
                        "k": k, "value": value, "component": "eps_model",
                        "grouping": {"instance_id": case.instance_id, "generator_id": gen_id},
                    })
            done += 1
            if done == 1 or done % 5 == 0 or done == total:
                print(f"[run] generation {done}/{total} (current: {gen_id})", flush=True)
    return art


def _jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8"
    )


def write_run(
    runs_root: str | Path,
    *,
    run_id: str,
    experiment_id: str,
    artifacts: CellArtifacts,
    resolved_config: Mapping[str, Any],
    code_version: CodeVersion,
    environment: Mapping[str, Any],
    seeds: Mapping[str, int],
    inputs: Sequence[ArtifactRef],
    models: Sequence[ModelRef],
) -> Path:
    """Persist a write-once run directory with a valid §6 manifest."""
    run_dir = Path(runs_root) / experiment_id / run_id
    if run_dir.exists():
        raise RunDirectoryExists(f"{run_dir} exists — runs/ is write-once; mint a new run id")
    (run_dir / "artifacts").mkdir(parents=True)
    (run_dir / "logs").mkdir(parents=True)

    write_status(run_dir, Status.RUNNING)

    _jsonl(run_dir / "artifacts" / "explanations.jsonl", [e.to_dict() for e in artifacts.explanations])
    _jsonl(run_dir / "artifacts" / "claims.jsonl", [c.to_dict() for c in artifacts.claims])
    _jsonl(run_dir / "artifacts" / "metrics.jsonl", artifacts.metric_rows)

    resolved_yaml = yaml.safe_dump(dict(resolved_config), sort_keys=True)
    (run_dir / "config.resolved.yaml").write_text(resolved_yaml, encoding="utf-8")

    output_files = [
        OutputFile(path=f"artifacts/{name}", sha256=sha256_file(run_dir / "artifacts" / name))
        for name in ("explanations.jsonl", "claims.jsonl", "metrics.jsonl")
    ]
    now = datetime.now(timezone.utc).isoformat()
    manifest = Manifest(
        artifact_id=run_id,
        artifact_type="run",
        pipeline_stage="metrics",
        code_version=code_version,
        resolved_config_sha256=sha256_json(dict(resolved_config)),
        resolved_config_path="config.resolved.yaml",
        environment=dict(environment),
        start_utc=now,
        end_utc=now,
        status=Status.COMPLETE,
        experiment_id=experiment_id,
        inputs=list(inputs),
        randomness=dict(seeds),
        models=list(models),
        outputs=output_files,
    )
    write_manifest(run_dir, manifest)
    write_status(run_dir, Status.COMPLETE)
    return run_dir
