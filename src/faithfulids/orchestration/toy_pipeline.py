"""The 5-instance toy pipeline (L5).

A complete, offline, deterministic end-to-end run: a fixed linear detector, an
exact linear attribution (no ``shap``/GPU), B1 + B2 generation (B2 through the
ledger-backed *deterministic stub* LLM), the firewalled extractor, and
Layer-1/Layer-2 metrics. Same seed ⇒ byte-identical ``metrics.jsonl`` — this is
what the ``determinism-smoke`` CI gate runs twice and diffs.

The toy is NON-CITABLE by construction (tier ``toy``); ``mapping-completeness``
blocks any paper asset from referencing it.
"""

from __future__ import annotations

from pathlib import Path

from faithfulids.extraction import build as build_extractor
from faithfulids.framework import AttributionArtifact, attack_probability
from faithfulids.generation import get_generator
from faithfulids.llm import CallLedger, LLMClient
from faithfulids.llm.providers import DeterministicStubProvider
from faithfulids.metrics.layer2 import SimpleBackgroundErasure
from faithfulids.orchestration.config_loader import load_config
from faithfulids.orchestration.references import resolve_reference
from faithfulids.orchestration.runner import (
    Components,
    InstanceCase,
    run_cells,
    write_run,
)
from faithfulids.provenance import (
    ArtifactRef,
    CodeVersion,
    ModelRef,
    mint_run_id,
    resolve_code_version,
    sha256_json,
)

TOY_FEATURES = ["f0", "f1", "f2", "f3"]
TOY_WEIGHTS = {"f0": 0.30, "f1": -0.20, "f2": 0.15, "f3": 0.05}
TOY_BIAS = 0.40
TOY_BACKGROUND = {f: 0.0 for f in TOY_FEATURES}

# Five fixed instances (deterministic — no dataset, no randomness).
TOY_INSTANCES = [
    {"f0": 1.0, "f1": 0.0, "f2": 1.0, "f3": 0.0},
    {"f0": 0.0, "f1": 1.0, "f2": 0.0, "f3": 1.0},
    {"f0": 1.0, "f1": 1.0, "f2": 1.0, "f3": 1.0},
    {"f0": 0.5, "f1": 0.2, "f2": 0.8, "f3": 0.1},
    {"f0": 0.1, "f1": 0.9, "f2": 0.2, "f3": 0.7},
]


class ToyLinearDetector:
    """proba = clip(bias + Σ w_f x_f, 0, 1). Fully deterministic (framework.DetectorArtifact).

    Binary, but reports the per-class contract (queue #5.2): predict_proba returns
    ``[P(BENIGN), P(ATTACK)] = [1-p, p]`` per row, labelled by ``class_names``.
    """

    feature_names = tuple(TOY_FEATURES)
    class_names = ("BENIGN", "ATTACK")

    def _p_attack(self, rows):
        out = []
        for r in rows:
            p = TOY_BIAS + sum(TOY_WEIGHTS[f] * r[f] for f in TOY_FEATURES)
            out.append(min(1.0, max(0.0, p)))
        return out

    def predict_proba(self, rows):
        return [[1.0 - p, p] for p in self._p_attack(rows)]

    def predicted_class(self, rows):
        return [self.class_names[max(range(len(r)), key=r.__getitem__)]
                for r in self.predict_proba(rows)]


def toy_attribution(instance_id: str, fv: dict[str, float]) -> AttributionArtifact:
    """Exact attribution of the linear model under a zero interventional background."""
    values = tuple(TOY_WEIGHTS[f] * (fv[f] - TOY_BACKGROUND[f]) for f in TOY_FEATURES)
    return AttributionArtifact(
        instance_id=instance_id,
        feature_names=tuple(TOY_FEATURES),
        values=values,
        base_value=TOY_BIAS,
        method="toy_linear",
        exact=True,
        background_policy="interventional_zero",
    )


def _cases(detector: ToyLinearDetector) -> list[InstanceCase]:
    cases: list[InstanceCase] = []
    for i, fv in enumerate(TOY_INSTANCES):
        pred = attack_probability(detector, [fv])[0]  # TODO(#5.5): predicted-class prob
        cases.append(
            InstanceCase(
                instance_id=f"toy-{i}",
                feature_values=dict(fv),
                attribution=toy_attribution(f"toy-{i}", fv),
                detector_prediction=pred,
                predicted_class="attack" if pred >= 0.5 else "benign",
            )
        )
    return cases


def run_toy(
    runs_root: str | Path,
    *,
    code_version: CodeVersion | None = None,
    seed: int | None = None,
) -> Path:
    """Execute EXP-TOY-001 into ``runs_root`` and return the run directory."""
    detector = ToyLinearDetector()
    cases = _cases(detector)

    ledger = CallLedger(Path(runs_root) / "_toy_llm_cache")
    client = LLMClient(DeterministicStubProvider(), ledger, mode="live")
    toy_llm = {
        "id": "toy_llm", "model_family": "llama3",
        "provider": "local_open_weights", "weights": {"revision": "pin-pending"},
    }

    b1 = get_generator(load_config("generator", "b1_template"))
    b2 = get_generator(load_config("generator", "b2_zeroshot"), llm_client=client, model_config=toy_llm)
    b3 = get_generator(load_config("generator", "b3_dte_style"), llm_client=client, model_config=toy_llm)
    generators = [("b1_template", b1), ("b2_zeroshot", b2), ("b3_dte_style", b3)]

    extcfg = load_config("extraction", "eval_extractor")
    extractor = build_extractor(
        extcfg, llm_client=client, model_config={**extcfg["model"], "id": extcfg["id"]},
        feature_vocabulary=TOY_FEATURES,
    )

    components = Components(
        detector=detector, extractor=extractor,
        erasure=SimpleBackgroundErasure(TOY_BACKGROUND),
        dataset_id="toy_smoke", layer1_top_k=3, layer2_k_values=[1, 3],
    )

    toy_seeds = resolve_reference("seeds:toy")
    gen_seed = seed if seed is not None else int(toy_seeds["generation"])
    artifacts = run_cells(cases, generators, components, seed=gen_seed)

    if code_version is None:
        # dirty worktree is allowed for the toy (debug mode) -> NON-CITABLE stamp
        from faithfulids.provenance import repo_root
        code_version = resolve_code_version(repo_root(), allow_dirty=True)

    environment = {"environment_hash": sha256_json({"toy": True, "python": "cpython"})}
    resolved_config = {
        "experiment": "EXP-TOY-001", "dataset": "toy_smoke", "detector": "toy_linear",
        "attribution": "toy_linear", "generators": ["b1_template", "b2_zeroshot", "b3_dte_style"],
        "layer1_top_k": 3, "layer2_k_values": [1, 3], "seed": gen_seed,
    }
    run_id = mint_run_id("EXP-TOY-001", code_version)
    inputs = [ArtifactRef("dataset:toy_smoke", sha256_json(TOY_INSTANCES), kind="dataset")]
    models = [
        ModelRef("detector", "toy_linear@fixed"),
        ModelRef("llm", f"stub@{DeterministicStubProvider.snapshot_id}"),
        ModelRef("extractor", f"{extcfg['model']['model_family']}@pin-pending"),
    ]
    return write_run(
        runs_root, run_id=run_id, experiment_id="EXP-TOY-001", artifacts=artifacts,
        resolved_config=resolved_config, code_version=code_version, environment=environment,
        seeds={"generation": gen_seed}, inputs=inputs, models=models,
    )
