"""Real experiment execution for the pilot vertical slice (L5).

Wires the full stage sequence for ``EXP-PILOT-001`` on real data:

    load CICIDS2017 -> sample -> train XGBoost -> TreeSHAP -> B0..B4 generation
    -> rule-assisted extraction -> Layer-1/Layer-2/cost metrics -> write run.

Everything is resolved from configs and injected, so the heavy pieces
(xgboost / shap / transformers) are pulled in lazily and can be substituted for
tests (RandomForest + a stub attributor + the deterministic stub LLM), while
Kaggle uses the real ones. Pilot instruments: the extractor runs rule-assisted
(no model) and B4's verifier is rule-based, so only ONE LLM is loaded — a
documented, firewall-preserving pilot simplification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from faithfulids.datasets.loaders.cicids2017 import (
    feature_columns,
    load_cicids2017,
    stratified_explanation_sample,
)
from faithfulids.extraction import build as build_extractor
from faithfulids.generation import get_generator
from faithfulids.generation.b4_vte.kb_retrieval import load_feature_semantics
from faithfulids.generation.b4_vte.verifier import RuleVerifier
from faithfulids.llm import CallLedger, LLMClient
from faithfulids.metrics.cost import cost_accounting
from faithfulids.metrics.layer2 import ConditionalExpectationImputer
from faithfulids.orchestration.config_loader import load_config
from faithfulids.orchestration.references import resolve_reference
from faithfulids.orchestration.registry import load_experiment
from faithfulids.orchestration.runner import Components, InstanceCase, run_cells, write_run
from faithfulids.provenance import (
    ArtifactRef,
    CodeVersion,
    ModelRef,
    mint_run_id,
    repo_root,
    resolve_code_version,
    sha256_file,
    sha256_json,
)

_LAYER2_K = [1, 3, 5]


def _data_input_refs(data_dir: Path) -> list[ArtifactRef]:
    refs: list[ArtifactRef] = []
    for csv in sorted(data_dir.rglob("*.csv")):
        refs.append(ArtifactRef(f"dataset:cicids2017:{csv.name}", sha256_file(csv), kind="dataset"))
    return refs


def run_pilot(
    experiment_id: str,
    *,
    data_dir: str | Path,
    runs_root: str | Path,
    seed: int | None = None,
    n_explain: int | None = None,
    max_rows: int | None = None,
    code_version: CodeVersion | None = None,
    detector_family: str | None = None,
    detector_hyperparameters: dict | None = None,
    attributor: Any | None = None,
    llm_provider: Any | None = None,
    data_loader: Callable[..., Any] | None = None,
) -> Path:
    """Execute the pilot vertical slice on real data and return the run dir."""
    from faithfulids.detectors import get_trainer, load_frozen  # lazy (no torch/xgb import)

    exp = load_experiment(experiment_id)
    axes = exp["design"]["axes"]
    dataset_id = axes["datasets"][0]
    detector_id = axes["detectors"][0]
    llm_id = axes["llms"][0]
    generator_ids = axes["generators"]

    dcfg = load_config("dataset", dataset_id)
    detcfg = load_config("detector", detector_id)
    llmcfg = load_config("llm", llm_id)
    attr_id = detcfg["attribution_ref"].split(":", 1)[1]
    attrcfg = load_config("attribution", attr_id)
    seeds = resolve_reference(exp["seed_ref"])
    gen_seed = seed if seed is not None else int(seeds["generation"])
    if n_explain is None:
        n_explain = int(load_config("sampling", "pilot_n150")["n_per_dataset"])

    # -- data --------------------------------------------------------------- #
    loader = data_loader or load_cicids2017
    df = loader(data_dir, max_rows=max_rows)
    feat_cols = feature_columns(df)
    train_df, explain_df = stratified_explanation_sample(
        df, n_explain=n_explain, seed=int(seeds["split"]),
        minority_floor=int(load_config("sampling", "pilot_n150")["minority_floor"]),
    )

    # -- detector (train -> frozen -> load) --------------------------------- #
    family = detector_family or detcfg["family"]
    hyper = detector_hyperparameters or detcfg["hyperparameters"]
    model_dir = Path(runs_root) / "_pilot_models" / f"{family}__{dataset_id}"
    get_trainer(family)(
        train_df[feat_cols + ["label"]], label_column="label",
        hyperparameters=hyper, seed=int(seeds["detector_training"]), out_dir=model_dir,
    )
    detector = load_frozen(family, model_dir)
    feature_names = list(detector.feature_names)

    instances = [{f: float(r[f]) for f in feature_names} for _, r in explain_df.iterrows()]
    ids = [f"cic-{i}" for i in range(len(instances))]

    # -- attribution (exact TreeSHAP) --------------------------------------- #
    if attributor is None:
        from faithfulids.attribution import get_attributor

        attributor = get_attributor(
            attrcfg["method"], background_policy=attrcfg["background_policy"]["removal_semantics"]
        )
    attributions = attributor.attribute(detector, instances, ids)
    preds = list(detector.predict_proba(instances))
    cases = [
        InstanceCase(
            instance_id=ids[i], feature_values=instances[i], attribution=attributions[i],
            detector_prediction=float(preds[i]),
            predicted_class="attack" if preds[i] >= 0.5 else "benign",
        )
        for i in range(len(instances))
    ]

    # -- LLM client (ONE model) + generators -------------------------------- #
    from faithfulids.llm.providers import TransformersProvider

    provider = llm_provider or TransformersProvider()
    ledger = CallLedger(Path(runs_root) / "_pilot_llm_cache")
    client = LLMClient(provider, ledger, mode="live")
    kb = load_feature_semantics(dataset_id)

    generators = []
    for gid in generator_ids:
        gcfg = load_config("generator", gid)
        if not gcfg["llm_dependent"]:
            generators.append((gid, get_generator(gcfg)))
        elif gcfg["code"] == "b4_vte":
            generators.append((gid, get_generator(
                gcfg, llm_client=client, model_config=llmcfg,
                kb_feature_semantics=kb, verifier=RuleVerifier(),
            )))
        else:
            generators.append((gid, get_generator(gcfg, llm_client=client, model_config=llmcfg)))

    # -- extractor (rule-assisted, no model) + erasure (fitted on train) ---- #
    extcfg = load_config("extraction", "eval_extractor")
    extractor = build_extractor(extcfg, llm_client=None, model_config=None, feature_vocabulary=feature_names)
    erasure = ConditionalExpectationImputer(k=5).fit(train_df[feature_names].to_numpy(), feature_names)

    top_k = int(load_config("generator", "b1_template")["params"]["top_k"])
    components = Components(
        detector=detector, extractor=extractor, erasure=erasure,
        dataset_id=dataset_id, layer1_top_k=top_k, layer2_k_values=_LAYER2_K,
    )
    artifacts = run_cells(cases, generators, components, seed=gen_seed)

    # -- cost accounting ---------------------------------------------------- #
    records = list(ledger.index.values())
    abstentions = [e.abstained for e in artifacts.explanations]
    for name, value in cost_accounting(records, abstentions).items():
        if isinstance(value, (int, float)):
            artifacts.metric_rows.append({
                "instance_id": "__aggregate__", "layer": "cost", "metric": name,
                "value": float(value), "grouping": {},
            })

    # -- write the run ------------------------------------------------------ #
    if code_version is None:
        code_version = resolve_code_version(repo_root(), allow_dirty=True)
    resolved_config = {
        "experiment": experiment_id, "dataset": dataset_id, "detector": family,
        "attribution": attrcfg["method"], "llm": llm_id, "generators": generator_ids,
        "n_explain": len(instances), "n_train": int(len(train_df)),
        "layer1_top_k": top_k, "layer2_k_values": _LAYER2_K, "seed": gen_seed,
        "extractor": "rule_assisted", "verifier": "rule_verifier",
        "pilot_note": "pilot-grade cleaning + rule-assisted extractor/verifier; NON-CITABLE",
    }
    run_id = mint_run_id(experiment_id, code_version)
    inputs = _data_input_refs(Path(data_dir))
    model_sha = sha256_file(model_dir / "model.bin") if (model_dir / "model.bin").is_file() else "0" * 64
    models = [
        ModelRef("detector", f"{family}@{model_sha[:12]}"),
        ModelRef("llm", f"{llm_id}@{(llmcfg.get('weights') or {}).get('revision','?')}",
                 quantisation=llmcfg.get("quantisation")),
        ModelRef("extractor", "rule_assisted@deterministic"),
    ]
    environment = {"environment_hash": sha256_json({"pilot": True, "family": family})}
    return write_run(
        runs_root, run_id=run_id, experiment_id=experiment_id, artifacts=artifacts,
        resolved_config=resolved_config, code_version=code_version, environment=environment,
        seeds={k: int(v) for k, v in seeds.items()}, inputs=inputs, models=models,
    )
