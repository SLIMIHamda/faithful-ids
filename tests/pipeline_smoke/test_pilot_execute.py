"""Pilot real-execution wiring, exercised locally with light substitutes.

Runs the full ``run_pilot`` orchestration (load -> sample -> train -> attribute
-> B0..B4 -> extract -> metrics -> write run) using RandomForest, a stub
attributor, and the deterministic stub LLM on a synthetic CICIDS2017-shaped CSV.
On Kaggle the same path uses XGBoost + TreeSHAP + a real transformers LLM.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from faithfulids.framework import AttributionArtifact
from faithfulids.llm.providers import DeterministicStubProvider
from faithfulids.orchestration.execute import run_pilot
from faithfulids.provenance import CodeVersion, Status, read_manifest, read_status, verify_outputs
from faithfulids.results import is_complete_and_verified, load_metrics

CV = CodeVersion("0" * 40, dirty=False)


class StubAttributor:
    """Deterministic stand-in for TreeSHAP (uses RF feature importances)."""

    def attribute(self, detector, instances, ids):
        fn = list(detector.feature_names)
        imp = getattr(detector.native_model, "feature_importances_", None)
        out = []
        for iid, inst in zip(ids, instances):
            if imp is not None:
                vals = tuple(float(imp[j] * inst[f]) for j, f in enumerate(fn))
            else:
                vals = tuple(float(inst[f]) for f in fn)
            out.append(AttributionArtifact(iid, tuple(fn), vals, 0.5, "stub", True, "stub"))
        return out


def _synthetic_cicids(path, n=400, seed=0):
    rng = np.random.RandomState(seed)
    attack = rng.rand(n) < 0.4
    feats = {f"f{j}": rng.rand(n) for j in range(6)}
    # f0, f2 cleanly separate the classes (margin around the 1.0 boundary) so the
    # detector is genuinely competent and the competence gate passes deterministically.
    feats["f0"] = np.where(attack, rng.uniform(0.7, 1.0, n), rng.uniform(0.0, 0.3, n))
    feats["f2"] = np.where(attack, rng.uniform(0.7, 1.0, n), rng.uniform(0.0, 0.3, n))
    df = pd.DataFrame(feats)
    df["Label"] = np.where(attack, "DoS Hulk", "BENIGN")
    df.to_csv(path, index=False)


def test_pilot_execute_end_to_end(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _synthetic_cicids(data_dir / "day1.csv", n=400)

    run_dir = run_pilot(
        "EXP-PILOT-001",
        data_dir=data_dir,
        runs_root=tmp_path / "runs",
        seed=8005,
        n_explain=40,
        code_version=CV,
        detector_family="random_forest",
        detector_hyperparameters={"n_estimators": 15, "max_depth": 4, "n_jobs": 1},
        attributor=StubAttributor(),
        llm_provider=DeterministicStubProvider(),
    )

    assert read_status(run_dir) is Status.COMPLETE
    assert read_manifest(run_dir).status is Status.COMPLETE
    assert verify_outputs(run_dir) == []

    run_id = run_dir.name
    assert is_complete_and_verified(run_id, runs_root=tmp_path / "runs")
    rows = load_metrics(run_id, runs_root=tmp_path / "runs")

    # all five generators represented in Layer-1
    gens = {r["grouping"].get("generator_id") for r in rows if r["layer"] == "layer1"}
    assert {"b0_raw_shap", "b1_template", "b2_zeroshot", "b3_dte_style", "b4_vte"} <= gens
    # Layer-2 (model-level) and cost rows present
    assert any(r["layer"] == "layer2" for r in rows)
    assert any(r["layer"] == "cost" and r["metric"] == "coverage" for r in rows)
    # B1 is faithful-by-construction -> its mean mention_f1 exceeds the free-form
    # stub generators' (a real, interpretable signal even in the wiring test)
    def mean_f1(g):
        vals = [r["value"] for r in rows
                if r["layer"] == "layer1" and r["metric"] == "mention_f1"
                and r["grouping"].get("generator_id") == g]
        return sum(vals) / len(vals) if vals else 0.0
    assert mean_f1("b1_template") >= mean_f1("b2_zeroshot")

    # ε_model (claim-driven) Layer-2 rows are emitted per generator (ADR-0001)
    eps_model = [r for r in rows if r["layer"] == "layer2" and r.get("component") == "eps_model"]
    assert eps_model and all("generator_id" in r["grouping"] for r in eps_model)

    # detector competence gate ran on the held-out explanation set and passed
    resolved = yaml.safe_load((run_dir / "config.resolved.yaml").read_text(encoding="utf-8"))
    comp = resolved["detector_competence"]
    assert comp["gate_passed"] is True
    assert comp["macro_f1"] >= comp["macro_f1_min"]
    assert set(comp["per_family_recall"]) >= {"BENIGN", "DoS Hulk"}
