"""EXP-G-002 — RQ0 metric-calibration gate execution (L5).

Token-free and LLM-free: B1 is faithful by construction, so its claim sets are
ground truth; the six registered corruption operators inject KNOWN errors with
labels, and each metric is scored as a corruption *detector*. Matched-pairs
criterion (user decision 2026-07-17): a corruption is structurally invisible to
some metrics, so each operator DESIGNATES its detector metrics
(``detector_metrics`` in ``configs/corruption/rq0_operators.yaml``); a metric is
admissible iff, at its recorded ROC operating point (max Youden's J), it reaches
sens >= rq0_sensitivity on every operator it is designated for AND
spec >= rq0_specificity on faithful items. Operators with an empty designation
are DOCUMENTED BLIND SPOTS: reported, non-blocking. The run's manifest carries
``gate: PASSED/FAILED`` — the token that unlocks gate-dependent experiments.

The recorded gate run executes on Kaggle against the K-way XGBoost detector
(default ``detector_id_override = xgboost_multiclass``): the Layer-2 cited
metrics are then calibrated on the same detector regime Tier-A uses. The
fluency-correlation half of RQ0 needs LLM texts and a judge; this claim-level
battery cannot measure it (documented in the run config).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from faithfulids.corruption import apply_operator
from faithfulids.datasets.loaders.cicids2017 import (
    feature_columns,
    load_cicids2017,
    multiclass_frame,
    stratified_explanation_sample,
)
from faithfulids.framework import ClaimSet, GenerationContext
from faithfulids.generation.b1_template import B1Template
from faithfulids.metrics.layer1 import compute_all as layer1_all
from faithfulids.metrics.layer2 import ConditionalExpectationImputer
from faithfulids.metrics.layer2.metrics import compute_eps_model
from faithfulids.metrics.meta import find_operating_point, roc_auc
from faithfulids.orchestration.config_loader import load_config
from faithfulids.orchestration.execute import _prediction_view
from faithfulids.orchestration.references import resolve_reference
from faithfulids.orchestration.runner import CellArtifacts, write_run
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

#: metric -> lower_is_corrupt. A working faithfulness metric scores corrupted
#: explanations LOWER; rate-of-badness metrics (hfr) score them HIGHER, and
#: sufficiency is a lower-is-better metric so corruption RAISES it.
POLARITY: dict[str, bool] = {
    "mention_precision": True, "mention_recall": True, "mention_f1": True,
    "dsa": True, "dsa_asserted": True, "direction_assertion_rate": True,
    "arc": True, "arc_n_pairs": True,
    "hfr": False,
    "comprehensiveness_cited": True, "comprehensiveness_cited_per_feature": True,
    "sufficiency_cited": False, "sufficiency_cited_per_feature": False,
}

FAITHFUL = "faithful"


def _polarity(metric: str) -> bool:
    return POLARITY.get(metric.split("[", 1)[0], True)


def battery_summary(
    per_variant_scores: dict[str, dict[str, list[float]]],
    designations: dict[str, list[str]],
    *,
    sens_min: float,
    spec_min: float,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Pure verdict core (numpy-only, offline-testable).

    ``per_variant_scores``: {metric: {variant: [per-instance scores]}} where
    variant is ``"faithful"`` or an operator name. ``designations``:
    {operator: [designated metrics]}. Returns per-metric summaries (threshold,
    per-operator sensitivity, specificity, AUC, admissibility) and the gate
    verdict: PASSED iff every designated (metric, operator) pair reaches
    ``sens_min`` and every designated metric reaches ``spec_min``.
    """
    designated_ops: dict[str, list[str]] = {}
    for op, mets in designations.items():
        for m in mets:
            designated_ops.setdefault(m, []).append(op)

    summaries: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for metric, by_variant in sorted(per_variant_scores.items()):
        low = _polarity(metric)
        faithful = by_variant.get(FAITHFUL, [])
        ops = {v: s for v, s in by_variant.items() if v != FAITHFUL}
        pooled = list(faithful) + [x for s in ops.values() for x in s]
        labels = [0] * len(faithful) + [1] * sum(len(s) for s in ops.values())
        op_point = find_operating_point(pooled, labels, lower_is_corrupt=low)
        auc = roc_auc(pooled, labels, lower_is_corrupt=low) if 0 < sum(labels) < len(labels) else 0.5
        thr = op_point["threshold"]

        def _sens(scores: list[float]) -> float:
            if not scores:
                return 0.0
            hit = sum(1 for x in scores if (x < thr if low else x > thr))
            return hit / len(scores)

        per_op_sens = {op: _sens(s) for op, s in sorted(ops.items())}
        spec = (
            sum(1 for x in faithful if not (x < thr if low else x > thr)) / len(faithful)
            if faithful else 0.0
        )
        mine = designated_ops.get(metric.split("[", 1)[0], [])
        admissible = None
        if mine and "[" not in metric:  # designation applies to the plain metric name
            ok_sens = all(per_op_sens.get(op, 0.0) >= sens_min for op in mine)
            ok_spec = spec >= spec_min
            admissible = ok_sens and ok_spec
            if not ok_spec:
                failures.append(f"{metric}: specificity {spec:.3f} < {spec_min}")
            for op in mine:
                if per_op_sens.get(op, 0.0) < sens_min:
                    failures.append(
                        f"{metric}: sensitivity {per_op_sens.get(op, 0.0):.3f} < {sens_min} "
                        f"on designated operator {op}"
                    )
        summaries[metric] = {
            "lower_is_corrupt": low, "threshold": thr, "youden_j": op_point["youden_j"],
            "auc": auc, "specificity": spec, "per_operator_sensitivity": per_op_sens,
            "designated_operators": mine, "admissible": admissible,
        }

    blind_spots = sorted(op for op, mets in designations.items() if not mets)
    verdict = {
        "passed": not failures,
        "failures": sorted(failures),
        "blind_spot_operators": blind_spots,
        "admissible_metrics": sorted(
            m for m, s in summaries.items() if s["admissible"] is True
        ),
        "sens_min": sens_min, "spec_min": spec_min,
    }
    return summaries, verdict


def _data_input_refs(data_dir: Path) -> list[ArtifactRef]:
    return [
        ArtifactRef(f"dataset:cicids2017:{csv.name}", sha256_file(csv), kind="dataset")
        for csv in sorted(data_dir.rglob("*.csv"))
    ]


def run_rq0_gate(
    experiment_id: str = "EXP-G-002",
    *,
    data_dir: str | Path,
    runs_root: str | Path,
    n_instances: int | None = None,
    max_rows: int | None = None,
    rows_per_file: int | None = None,
    code_version: CodeVersion | None = None,
    detector_id_override: str | None = None,
    detector_family: str | None = None,
    detector_hyperparameters: dict | None = None,
    attributor: Any | None = None,
    data_loader: Callable[..., Any] | None = None,
) -> Path:
    """Execute the RQ0 calibration battery and write a gate-verdict run."""
    from faithfulids.detectors import get_trainer, load_frozen  # lazy (no xgb import)
    from faithfulids.orchestration.registry import load_experiment

    exp = load_experiment(experiment_id)
    corr_ref = exp["config_refs"]["corruption"]
    corrcfg = load_config("corruption", corr_ref.split(":", 1)[1])
    # Gate venue default: the K-way detector (calibrate on the Tier-A regime).
    detector_id = detector_id_override or "xgboost_multiclass"
    detcfg = load_config("detector", detector_id)
    seeds = resolve_reference(exp["seed_ref"])
    seed = int(seeds["rq0_calibration"])
    n_instances = n_instances or 60
    sens_min = float(resolve_reference("statistics:decision_thresholds:rq0_sensitivity")["value"])
    spec_min = float(resolve_reference("statistics:decision_thresholds:rq0_specificity")["value"])

    # -- data + detector (mirrors the pilot's K-way path) -------------------- #
    loader = data_loader or load_cicids2017
    loader_kwargs: dict[str, Any] = {"max_rows": max_rows}
    if rows_per_file is not None:
        loader_kwargs["rows_per_file"] = rows_per_file
    df = loader(data_dir, **loader_kwargs)
    feat_cols = feature_columns(df)
    hyper = detector_hyperparameters or detcfg["hyperparameters"]
    family = detector_family or detcfg["family"]
    multiclass = str(hyper.get("objective", "")).startswith("multi:")
    train_df, explain_df = stratified_explanation_sample(
        df, n_explain=n_instances, seed=seed,
        stratify="target_class" if multiclass else "attack_class",
        truncation="round_robin" if multiclass else "index",
    )
    model_dir = Path(runs_root) / "_gate_models" / f"{family}__rq0"
    if multiclass:
        train_mc, class_idx = multiclass_frame(train_df)
        explain_df, _ = multiclass_frame(explain_df)
        class_names = [c for c, _ in sorted(class_idx.items(), key=lambda kv: kv[1])]
        if len(class_names) < 3:
            raise ValueError(
                f"RQ0 gate degenerated to {len(class_names)} classes {class_names}: "
                "raise/unset max_rows or use rows_per_file so every family loads."
            )
        get_trainer(family)(
            train_mc[feat_cols + ["target_index"]], label_column="target_index",
            hyperparameters=hyper, seed=seed, out_dir=model_dir, class_names=class_names,
        )
    else:
        get_trainer(family)(
            train_df[feat_cols + ["label"]], label_column="label",
            hyperparameters=hyper, seed=seed, out_dir=model_dir,
        )
    detector = load_frozen(family, model_dir)
    feature_names = list(detector.feature_names)
    instances = [{f: float(r[f]) for f in feature_names} for _, r in explain_df.iterrows()]
    ids = [f"rq0-{i}" for i in range(len(instances))]

    if attributor is None:
        from faithfulids.attribution import get_attributor

        attrcfg = load_config("attribution", detcfg["attribution_ref"].split(":", 1)[1])
        attributor = get_attributor(
            attrcfg["method"], background_policy=attrcfg["background_policy"]["removal_semantics"]
        )
    attributions = attributor.attribute(detector, instances, ids)
    preds, pred_classes = _prediction_view(detector, instances)
    erasure = ConditionalExpectationImputer(k=5).fit(train_df[feature_names].to_numpy(), feature_names)
    spaces = load_config("metric", "layer2_erasure").get("delta_spaces", ["prob"])

    # -- battery: faithful B1 claims + 6 corruptions per instance ------------ #
    b1 = B1Template(int(load_config("generator", corrcfg["base_generator"])["params"]["top_k"]))
    designations = {
        op["name"]: list(op.get("detector_metrics", [])) for op in corrcfg["operators"]
    }
    art = CellArtifacts()
    per_variant: dict[str, dict[str, list[float]]] = {}

    def _record(variant: str, label: int, iid: str, claims: ClaimSet, i: int) -> None:
        vals = dict(layer1_all(claims, attributions[i], top_k=b1.top_k))
        for space in spaces:
            for name, v in compute_eps_model(
                claims, detector, instances[i], erasure, k=5, delta_space=space
            ).items():
                vals[f"{name}[{space}]"] = v
        for name, v in vals.items():
            per_variant.setdefault(name, {}).setdefault(variant, []).append(float(v))
            art.metric_rows.append({
                "instance_id": iid, "layer": "rq0", "metric": name, "value": float(v),
                "grouping": {"variant": variant, "label": label},
            })

    for i, iid in enumerate(ids):
        ctx = GenerationContext(
            instance_id=iid, feature_values=instances[i], attribution=attributions[i],
            detector_prediction=float(preds[i]), predicted_class=pred_classes[i],
            dataset_id="cicids2017_corrected",
            score_label="attack" if len(detector.class_names) == 2
            else (attributions[i].explained_class or pred_classes[i]),
        )
        art.explanations.append(b1.generate(ctx))
        faithful = ClaimSet(
            instance_id=iid, claims=b1.faithful_claims(ctx),
            extractor_id="b1_construction", extractor_version="1.0.0",
            prompt_sha256="0" * 64,
        )
        art.claims.append(faithful)
        _record(FAITHFUL, 0, iid, faithful, i)
        for op in corrcfg["operators"]:
            res = apply_operator(op["name"], faithful, op.get("params"))
            _record(res.operator, 1, iid, res.claims, i)

    # -- verdict + run -------------------------------------------------------- #
    summaries, verdict = battery_summary(
        per_variant, designations, sens_min=sens_min, spec_min=spec_min
    )
    for metric, s in summaries.items():
        art.metric_rows.append({
            "instance_id": "__aggregate__", "layer": "rq0_meta", "metric": metric,
            "value": float(s["auc"]), "grouping": {k: v for k, v in s.items() if k != "auc"},
        })
    art.metric_rows.append({
        "instance_id": "__aggregate__", "layer": "rq0_meta", "metric": "gate_verdict",
        "value": 1.0 if verdict["passed"] else 0.0, "grouping": verdict,
    })
    (model_dir / "rq0_verdict.json").write_text(
        json.dumps({"verdict": verdict, "summaries": summaries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if code_version is None:
        code_version = resolve_code_version(repo_root(), allow_dirty=True)
    resolved_config = {
        "experiment": experiment_id, "detector": detector_id, "detector_family": family,
        "n_instances": len(instances), "n_train": int(len(train_df)),
        "max_rows": max_rows, "rows_per_file": rows_per_file,
        "operators": sorted(designations), "designations": designations,
        "criterion": "matched_pairs@roc_operating_point",
        "sens_min": sens_min, "spec_min": spec_min,
        "delta_spaces": list(spaces), "layer2_k": 5, "seed": seed,
        "gate_passed": verdict["passed"],
        "note": (
            "claim-level battery: fluency correlation needs LLM texts + judge and "
            "is out of scope here; magnitude_inflation is a documented blind spot."
        ),
    }
    model_sha = sha256_file(model_dir / "model.bin") if (model_dir / "model.bin").is_file() else "0" * 64
    return write_run(
        runs_root, run_id=mint_run_id(experiment_id, code_version),
        experiment_id=experiment_id, artifacts=art, resolved_config=resolved_config,
        code_version=code_version,
        environment={"environment_hash": sha256_json({"gate": "rq0", "family": family})},
        seeds={"rq0_calibration": seed}, inputs=_data_input_refs(Path(data_dir)),
        models=[ModelRef("detector", f"{family}@{model_sha[:12]}")],
        gate="PASSED" if verdict["passed"] else "FAILED",
    )
