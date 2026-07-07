#!/usr/bin/env python
"""Layer-2 saturation diagnostic CLI (pinned env).

Recomputes ε_att and ε_model comprehensiveness+sufficiency in probability AND
margin (log-odds) space over a completed pilot run's re-derived instances, to
distinguish probability *saturation* (near-certain detector) from a broken
erasure. It re-derives the run's inputs from the run's own recorded config +
seeds, reuses the run's cached claims (mints NO new LLM tokens), and NEVER mutates
the source run — it writes a standalone report.

Requires the scientific stack (xgboost/shap) and the CICIDS2017 data, so it runs
on Kaggle / the pinned container, not in local CPU tests. The pure summary core
(``faithfulids.metrics.layer2.saturation.saturation_report``) is unit-tested
offline. Pair with the erasure-efficacy CI test: that rules out a no-op erasure;
this quantifies saturation given a working one.

Usage:
  python tools/layer2_saturation_diagnostic.py \
      --experiment EXP-PILOT-001 --run-id <run_id> --data-dir <cicids_dir> \
      --runs-root runs --out analysis/outputs/pilot_layer2_saturation/results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Layer-2 saturation diagnostic")
    ap.add_argument("--experiment", default="EXP-PILOT-001")
    ap.add_argument("--run-id", required=True, help="source run id under runs-root/<experiment>/")
    ap.add_argument("--data-dir", required=True, help="CICIDS2017 CSV directory")
    ap.add_argument("--runs-root", default="runs")
    ap.add_argument("--out", required=True, help="output report JSON (a new file; source run untouched)")
    ap.add_argument("--k", type=int, nargs="+", default=[1, 3, 5])
    args = ap.parse_args()

    # Heavy imports (scientific stack) kept local to main so importing this module
    # never drags in xgboost / shap.
    import yaml

    from faithfulids.attribution import get_attributor
    from faithfulids.datasets.loaders.cicids2017 import (
        feature_columns,
        load_cicids2017,
        stratified_explanation_sample,
    )
    from faithfulids.detectors import load_frozen
    from faithfulids.framework import ClaimSet
    from faithfulids.metrics.layer2 import ConditionalExpectationImputer
    from faithfulids.metrics.layer2.saturation import saturation_report
    from faithfulids.orchestration.config_loader import load_config
    from faithfulids.orchestration.registry import load_experiment

    run_root = Path(args.runs_root) / args.experiment / args.run_id
    resolved = yaml.safe_load((run_root / "config.resolved.yaml").read_text(encoding="utf-8"))
    manifest = json.loads((run_root / "MANIFEST.json").read_text(encoding="utf-8"))
    seeds = manifest["randomness"]  # exact per-stage seeds used by the source run

    exp = load_experiment(args.experiment)
    dataset_id = exp["design"]["axes"]["datasets"][0]
    detector_id = exp["design"]["axes"]["detectors"][0]
    detcfg = load_config("detector", detector_id)
    attrcfg = load_config("attribution", detcfg["attribution_ref"].split(":", 1)[1])
    sampling = load_config("sampling", "pilot_n150")

    # Re-derive the identical explanation set from the source run's config + seeds.
    df = load_cicids2017(args.data_dir)
    feat_cols = feature_columns(df)
    _train_df, explain_df = stratified_explanation_sample(
        df,
        n_explain=int(resolved["n_explain"]),
        seed=int(seeds["split"]),
        minority_floor=int(sampling["minority_floor"]),
    )

    family = detcfg["family"]
    model_dir = Path(args.runs_root) / "_pilot_models" / f"{family}__{dataset_id}"
    detector = load_frozen(family, model_dir)
    feature_names = list(detector.feature_names)

    ids = [f"cic-{i}" for i in range(len(explain_df))]
    instances = {
        ids[i]: {f: float(r[f]) for f in feature_names}
        for i, (_, r) in enumerate(explain_df.iterrows())
    }

    attributor = get_attributor(
        attrcfg["method"], background_policy=attrcfg["background_policy"]["removal_semantics"]
    )
    attr_list = attributor.attribute(detector, list(instances.values()), ids)
    attributions = {iid: a for iid, a in zip(ids, attr_list)}

    erasure = ConditionalExpectationImputer(k=5).fit(
        _train_df[feature_names].to_numpy(), feature_names
    )

    # Rebuild {(instance_id, generator_id): ClaimSet} by zipping the run's
    # explanations (carry generator_id) with its claims (written in lockstep).
    art = run_root / "artifacts"
    exps = [json.loads(l) for l in art.joinpath("explanations.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    clms = [json.loads(l) for l in art.joinpath("claims.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    claims_map = {
        (e["instance_id"], e["generator_id"]): ClaimSet.from_dict(c) for e, c in zip(exps, clms)
    }

    report = saturation_report(
        detector, instances, attributions, claims_map, erasure, k_values=list(args.k)
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "diagnostic": "layer2_saturation",
                "source_run": f"{args.experiment}/{args.run_id}",
                "note": "Read-only re-derivation of the source run's inputs; the source run is not mutated.",
                "k_values": list(args.k),
                "report": report,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[layer2-saturation] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
