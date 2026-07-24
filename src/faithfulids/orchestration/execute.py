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

import json
from pathlib import Path
from typing import Any, Callable

from faithfulids.datasets.loaders.cicids2017 import (
    feature_columns,
    load_cicids2017,
    multiclass_frame,
    stratified_explanation_sample,
)
from faithfulids.extraction import build as build_extractor
from faithfulids.framework import attack_probability
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

def _prediction_view(detector, instances):
    """(score, class-name) per instance for the GenerationContext (queue #5.5).

    Multi-class: the argmax class NAME and ITS probability — what an analyst is
    actually told, and what the attribution/Layer-2 are about (#5.3/#5.4).

    Binary: the attack probability with the literal 'attack'/'benign' strings,
    UNCHANGED. These land in the generation prompt, so renaming them would change
    every LLM request hash and break token-free replay of the cached binary runs.
    """
    names = tuple(detector.class_names)
    if len(names) == 2:
        p = list(attack_probability(detector, instances))
        return p, ["attack" if x >= 0.5 else "benign" for x in p]
    proba = detector.predict_proba(instances)
    predicted = list(detector.predicted_class(instances))
    scores = [float(row[names.index(c)]) for row, c in zip(proba, predicted)]
    return scores, predicted


_LAYER2_K = [1, 3, 5]

#: Rows per prediction batch on the competence split. That split is the whole
#: held-out remainder (~100k rows at Tier-A scale) and ``predict_proba`` builds a
#: dense list-of-lists, so it is consumed in chunks to bound peak memory. Purely
#: an execution detail — chunking changes no statistic.
_COMPETENCE_CHUNK = 20_000


def _competence_view(
    detector, df, feature_names: list[str], multiclass: bool
) -> tuple[list[str] | None, list[float] | None]:
    """Predictions over the competence split, in chunks.

    Returns ``(predicted_class_names, None)`` for a K-way detector and
    ``(None, attack_probabilities)`` for a binary one — each gate table needs
    exactly one of the two, and computing both would double the work on the
    largest frame in the run.
    """
    names: list[str] = []
    probs: list[float] = []
    for start in range(0, len(df), _COMPETENCE_CHUNK):
        chunk = df.iloc[start:start + _COMPETENCE_CHUNK]
        rows = [{f: float(r[f]) for f in feature_names}
                for r in chunk[feature_names].to_dict("records")]
        if multiclass:
            names.extend(detector.predicted_class(rows))
        else:
            probs.extend(float(p) for p in attack_probability(detector, rows))
    return (names, None) if multiclass else (None, probs)


def _class_semantics(kb_name: str) -> dict[str, str]:
    """{canonical class -> KB profile} for B5's class grounding.

    ``kb/attack_classes/<kb_name>.yaml`` entries are granular family names
    ("DoS Hulk"); they aggregate to the CANONICAL classes the detector predicts
    through the single taxonomy config (#5.1b), so the snippet B5 cites is
    guaranteed to describe the class the attribution explains. Excluded families
    drop out. Binary runs' 'attack'/'benign' labels simply miss (B5 renders its
    neutral placeholder).
    """
    import yaml

    from faithfulids.datasets.loaders.cicids2017 import canonical_class

    path = repo_root() / "kb" / "attack_classes" / f"{kb_name}.yaml"
    if not path.is_file():
        return {}
    out: dict[str, list[str]] = {}
    for e in yaml.safe_load(path.read_text(encoding="utf-8")).get("entries", []):
        c = canonical_class(e["name"])
        if c is not None:
            out.setdefault(c, []).append(str(e["description"]).strip())
    return {c: " ".join(descs) for c, descs in out.items()}


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
    rows_per_file: int | None = None,
    code_version: CodeVersion | None = None,
    detector_family: str | None = None,
    detector_hyperparameters: dict | None = None,
    attributor: Any | None = None,
    llm_provider: Any | None = None,
    data_loader: Callable[..., Any] | None = None,
    enforce_competence: bool = True,
    llm_id_override: str | None = None,
    detector_id_override: str | None = None,
    generator_ids_override: list[str] | None = None,
    llm_mode: str = "live",
    llm_cache_dir: str | Path | None = None,
) -> Path:
    """Execute the pilot vertical slice on real data and return the run dir."""
    from faithfulids.detectors import get_trainer, load_frozen  # lazy (no torch/xgb import)

    exp = load_experiment(experiment_id)
    axes = exp["design"]["axes"]
    dataset_id = axes["datasets"][0]
    # One detector per run; detector_id_override selects the K-way detector
    # (queue #5.6) without editing the registered experiment.
    detector_id = detector_id_override or axes["detectors"][0]
    # One LLM per run (Kaggle memory). llm_id_override selects it per run so the
    # scale-test cell can run the pilot once per model and compare (e.g. 3B vs 7B).
    llm_id = llm_id_override or axes["llms"][0]
    # Override for REPLAY re-scores of runs generated under an older generator
    # axis: a generator added later (b5) has no ledger entries in those runs, so
    # replaying the current axis would hard-error on the first b5 cell. Pin the
    # original run's generator list (its resolved_config records it).
    generator_ids = list(generator_ids_override) if generator_ids_override else axes["generators"]

    dcfg = load_config("dataset", dataset_id)
    detcfg = load_config("detector", detector_id)
    llmcfg = load_config("llm", llm_id)
    attr_id = detcfg["attribution_ref"].split(":", 1)[1]
    attrcfg = load_config("attribution", attr_id)
    seeds = resolve_reference(exp["seed_ref"])
    gen_seed = seed if seed is not None else int(seeds["generation"])
    # The pilot seed section carries flat split/detector_training keys; Tier-A
    # sections route them through the canonical per-dataset `splits:` and
    # per-family `detector_training:` sections of the seed table.
    split_seed = (int(seeds["split"]) if "split" in seeds
                  else int(resolve_reference("seeds:splits")[dataset_id]))
    # Sampling protocol comes from the EXPERIMENT's first sampling ref (Tier-A
    # anchor = n400_stratified, spokes = n150_stratified); the pilot's first ref
    # is pilot_n150, so its resolved values are byte-identical to the historical
    # hard-coded lookup (replay safety).
    samp_id = (exp.get("sampling_refs") or ["sampling:pilot_n150"])[0].split(":", 1)[1]
    sampcfg = load_config("sampling", samp_id)
    if n_explain is None:
        n_explain = int(sampcfg["n_per_dataset"])

    # -- data --------------------------------------------------------------- #
    loader = data_loader or load_cicids2017
    loader_kwargs: dict[str, Any] = {"max_rows": max_rows}
    if rows_per_file is not None:  # only pass when set — injected test loaders may not accept it
        loader_kwargs["rows_per_file"] = rows_per_file
    df = loader(data_dir, **loader_kwargs)
    feat_cols = feature_columns(df)
    # K-way selector: a multi:* objective (xgboost) OR the config's task field
    # (families like random_forest have no objective hyperparameter to key on).
    _mc = (str((detector_hyperparameters or detcfg["hyperparameters"]).get("objective", "")
               ).startswith("multi:")
           or detcfg.get("task") == "multiclass")
    train_df, explain_df, competence_df = stratified_explanation_sample(
        df, n_explain=n_explain, seed=split_seed,
        minority_floor=int(sampcfg["minority_floor"]),
        # stratify on the K-way target so every canonical class is represented in the
        # explained set (binary keeps the historical attack_class stratification)
        stratify="target_class" if _mc else "attack_class",
        # K-way: over-quota picks are dropped evenly across classes — CICIDS classes
        # are contiguous per-day blocks, so the legacy lowest-index truncation can
        # erase late-day classes from the very set the per-class gate measures.
        # Binary keeps "index": it is what every cached run used (replay hashes).
        truncation="round_robin" if _mc else "index",
    )

    # -- detector (train -> frozen -> load) --------------------------------- #
    family = detector_family or detcfg["family"]
    det_seed = (int(seeds["detector_training"]) if "detector_training" in seeds
                else int(resolve_reference("seeds:detector_training")[family]))
    hyper = detector_hyperparameters or detcfg["hyperparameters"]
    model_dir = Path(runs_root) / "_pilot_models" / f"{family}__{dataset_id}"
    # queue #5.6: the K-way selector trains the target_index over the canonical
    # taxonomy and freezes class_names with the model; the binary path keeps the
    # untouched `label` column, so the existing pilot is bit-for-bit as before.
    multiclass = _mc
    if multiclass:
        train_mc, class_idx = multiclass_frame(train_df)
        explain_df, _ = multiclass_frame(explain_df)
        competence_df, _ = multiclass_frame(competence_df)
        class_names = [c for c, _ in sorted(class_idx.items(), key=lambda kv: kv[1])]
        if len(class_names) < 3:
            # A K<3 "multi-class" run silently re-creates the trivially separable
            # binary task this detector exists to replace (and straddles the
            # len(class_names)==2 binary-continuity branches with per-class SHAP).
            # The usual cause: a global max_rows keeps only the first day's CSV.
            raise ValueError(
                f"multi-class run degenerated to {len(class_names)} class(es) "
                f"{class_names}: the loaded rows cover too few attack families. "
                f"max_rows appends whole files in name order — use rows_per_file "
                f"(env FAITHFULIDS_ROWS_PER_FILE) or raise/unset max_rows so every "
                f"day's families load."
            )
        print(f"multi-class detector: {len(class_names)} classes {class_names}; "
              f"dropped {len(train_df) - len(train_mc)} excluded/rare train rows")
        get_trainer(family)(
            train_mc[feat_cols + ["target_index"]], label_column="target_index",
            hyperparameters=hyper, seed=det_seed, out_dir=model_dir,
            class_names=class_names,
        )
    else:
        get_trainer(family)(
            train_df[feat_cols + ["label"]], label_column="label",
            hyperparameters=hyper, seed=det_seed, out_dir=model_dir,
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
    preds, pred_classes = _prediction_view(detector, instances)
    cases = [
        InstanceCase(
            instance_id=ids[i], feature_values=instances[i], attribution=attributions[i],
            detector_prediction=float(preds[i]),
            predicted_class=pred_classes[i],
        )
        for i in range(len(instances))
    ]

    # -- detector competence gate (imbalance-aware; before any tokens) ------ #
    # Evaluated on the held-out COMPETENCE split — disjoint from the training
    # frame and from the explained set (prereg amendment 0001). Competence is a
    # property of the detector, and ~21 explained instances per class cannot
    # support a per-class recall floor (Wilson 95% half-width ≈ ±0.14 at p=0.8);
    # the competence split carries thousands per class at the natural prior. The
    # explained set's composition is reported alongside, never gated on.
    # Gated on macro-F1 AND the per-class recall floor AND per-class minimum
    # support: faithfulness on instances the model gets right by luck is noise.
    from faithfulids.detectors.competence import (
        DetectorNotCompetent, classification_table, evaluate_competence,
        family_support, multiclass_classification_table,
    )

    _kway = len(detector.class_names) > 2
    comp_names, comp_probs = _competence_view(detector, competence_df, feature_names, _kway)
    if _kway:
        # K-way: gate on "was it classified as the RIGHT family", not merely "as
        # some attack" — an explanation of a misattributed class explains the wrong
        # decision (queue #5.5).
        comp_table = multiclass_classification_table(
            [str(v) for v in competence_df["target_class"].tolist()], comp_names
        )
        explained_table = multiclass_classification_table(
            [str(v) for v in explain_df["target_class"].tolist()], pred_classes
        )
    else:
        comp_table = classification_table(
            [int(v) for v in competence_df["label"].tolist()],
            [1 if p >= 0.5 else 0 for p in comp_probs],
            [str(v) for v in competence_df["attack_class"].tolist()],
            y_score=comp_probs,
        )
        explained_table = classification_table(
            [int(v) for v in explain_df["label"].tolist()],
            [1 if p >= 0.5 else 0 for p in preds],
            [str(v) for v in explain_df["attack_class"].tolist()],
            y_score=preds,
        )
    macro_f1_min = float(resolve_reference("statistics:decision_thresholds:detector_macro_f1_min")["value"])
    recall_floor = float(resolve_reference("statistics:decision_thresholds:detector_recall_floor")["value"])
    min_support = int(resolve_reference("statistics:decision_thresholds:detector_class_min_support")["value"])
    exemptions = (detcfg.get("competence_gate") or {}).get("recall_floor_exemptions", [])
    comp = evaluate_competence(
        comp_table, macro_f1_min=macro_f1_min, recall_floor=recall_floor,
        exemptions=exemptions, min_support=min_support,
    )
    # competence.json keeps the GATE table at the top level (what the floor was
    # read from) and carries the explained set beside it, so a reader can never
    # mistake which set produced the verdict.
    comp_table["evaluation_set"] = "competence_holdout"
    comp_table["min_support"] = min_support
    comp_table["explained_set"] = {
        "n": int(len(explain_df)),
        "per_class_n": {f: family_support(r) for f, r in explained_table["per_family"].items()},
        "table": explained_table,
    }
    (model_dir / "competence.json").write_text(
        json.dumps(comp_table, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if enforce_competence and not comp.passed:
        raise DetectorNotCompetent(
            f"detector fails competence gate on the held-out competence split "
            f"(n={comp_table['n']}): macro_f1={comp.macro_f1:.3f} (min {macro_f1_min}); "
            f"AUC={comp_table['auc']}; attack families below recall floor "
            f"{recall_floor}: {[f for f, _ in comp.failures]}; below min support "
            f"{min_support}: {[f for f, _ in comp.under_support]}; "
            f"exemptions={list(comp.exemptions)}. Faithfulness on an incompetent "
            f"detector is meaningless — fix the detector, or resolve the failing "
            f"classes through the pre-registered contingency (amendment 0001)."
        )

    # -- LLM client (ONE model) + generators -------------------------------- #
    # Live: run the model. Replay: serve every generation from a pre-populated
    # ledger (no provider, no GPU, no tokens) — used to RE-SCORE a completed run
    # after an extractor/metric fix without regenerating. A replay cache miss is
    # a hard error (the ledger must already hold every call for these instances),
    # so N / max_rows / llm / seed must match the original run byte-for-byte.
    if llm_mode not in ("live", "replay"):
        raise ValueError("llm_mode must be 'live' or 'replay'")
    ledger = CallLedger(Path(llm_cache_dir) if llm_cache_dir else Path(runs_root) / "_pilot_llm_cache")
    if llm_mode == "replay":
        client = LLMClient(None, ledger, mode="replay")
    else:
        from faithfulids.llm.providers import TransformersProvider

        provider = llm_provider or TransformersProvider()
        client = LLMClient(provider, ledger, mode="live")
    # KB corpora are keyed by the dataset config's kb_ref NAME (kb:cicids2017@…),
    # not the dataset id: kb/feature_semantics/cicids2017.yaml exists,
    # cicids2017_corrected.yaml does not — so the historical dataset_id lookup
    # silently returned {} and every cached binary run's b4 prompt carried an
    # EMPTY "Feature meanings" section. That emptiness is now baked into those
    # runs' request hashes, so the binary path keeps it (token-free replay);
    # K-way runs resolve the KB name properly and get real grounding.
    kb_name = (dcfg.get("kb_ref") or f"kb:{dataset_id}@").split(":", 1)[1].split("@", 1)[0]
    kb = load_feature_semantics(kb_name if multiclass else dataset_id)

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
        elif gcfg["code"] == "b5_narrative_vte":
            generators.append((gid, get_generator(
                gcfg, llm_client=client, model_config=llmcfg,
                kb_feature_semantics=kb,
                kb_class_semantics=_class_semantics(kb_name),
                verifier=RuleVerifier(),
            )))
        else:
            generators.append((gid, get_generator(gcfg, llm_client=client, model_config=llmcfg)))

    # -- extractor (rule-assisted, no model) + erasure (fitted on train) ---- #
    extcfg = load_config("extraction", "eval_extractor")
    extractor = build_extractor(extcfg, llm_client=None, model_config=None, feature_vocabulary=feature_names)
    erasure = ConditionalExpectationImputer(k=5).fit(train_df[feature_names].to_numpy(), feature_names)

    top_k = int(load_config("generator", "b1_template")["params"]["top_k"])
    delta_spaces = load_config("metric", "layer2_erasure").get("delta_spaces", ["prob"])
    components = Components(
        detector=detector, extractor=extractor, erasure=erasure,
        dataset_id=dataset_id, layer1_top_k=top_k, layer2_k_values=_LAYER2_K,
        layer2_delta_spaces=tuple(delta_spaces),
    )
    artifacts = run_cells(cases, generators, components, seed=gen_seed)

    # -- cost accounting ---------------------------------------------------- #
    # tokens/latency/$ are run-global; coverage/abstention_rate belong ONLY to
    # abstention-capable generators (B4). Averaging abstention over all five
    # baselines made 24/60 read as 0.08 — scope the denominator to B4's cells.
    records = list(ledger.index.values())
    abst_capable = {
        gid for gid in generator_ids if load_config("generator", gid).get("abstention")
    }
    abstentions = [e.abstained for e in artifacts.explanations if e.generator_id in abst_capable]
    _scoped = {"coverage", "abstention_rate"}
    for name, value in cost_accounting(records, abstentions).items():
        if not isinstance(value, (int, float)):
            continue
        if name in _scoped and not abstentions:
            continue  # no abstention-capable generator in this run → undefined, omit
        grouping = (
            {"scope": "abstention_capable", "generators": sorted(abst_capable),
             "n_denominator": len(abstentions)}
            if name in _scoped else {}
        )
        artifacts.metric_rows.append({
            "instance_id": "__aggregate__", "layer": "cost", "metric": name,
            "value": float(value), "grouping": grouping,
        })

    # -- write the run ------------------------------------------------------ #
    if code_version is None:
        code_version = resolve_code_version(repo_root(), allow_dirty=True)
    resolved_config = {
        "experiment": experiment_id, "dataset": dataset_id, "detector": family,
        "attribution": attrcfg["method"], "llm": llm_id, "generators": generator_ids,
        "n_explain": len(instances), "n_train": int(len(train_df)),
        "max_rows": max_rows, "rows_per_file": rows_per_file,
        "layer1_top_k": top_k, "layer2_k_values": _LAYER2_K, "seed": gen_seed,
        "extractor": "rule_assisted", "verifier": "rule_verifier", "llm_mode": llm_mode,
        "detector_competence": {
            "evaluation_set": "competence_holdout",  # NOT the explained set (amendment 0001)
            "n_competence": int(len(competence_df)),
            "macro_f1": comp_table["macro_f1"], "auc": comp_table["auc"],
            "macro_f1_min": macro_f1_min, "recall_floor": recall_floor,
            "min_support": min_support,
            "gate_passed": comp.passed,
            "per_family_recall": {f: r["detection_recall"] for f, r in comp_table["per_family"].items()},
            "per_family_n": {f: family_support(r) for f, r in comp_table["per_family"].items()},
            "under_support": [f for f, _ in comp.under_support],
            "explained_per_class_n": comp_table["explained_set"]["per_class_n"],
            "exemptions": list(comp.exemptions),
        },
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
        seeds={**{k: int(v) for k, v in seeds.items()},
               "split": split_seed, "detector_training": det_seed},
        inputs=inputs, models=models,
    )
