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
        llm_id_override="mistral_7b_instruct",  # scale-test path: per-run LLM selection
    )

    assert read_status(run_dir) is Status.COMPLETE
    assert read_manifest(run_dir).status is Status.COMPLETE
    assert verify_outputs(run_dir) == []

    run_id = run_dir.name
    assert is_complete_and_verified(run_id, runs_root=tmp_path / "runs")
    rows = load_metrics(run_id, runs_root=tmp_path / "runs")

    # all six generators represented in Layer-1
    gens = {r["grouping"].get("generator_id") for r in rows if r["layer"] == "layer1"}
    assert {"b0_raw_shap", "b1_template", "b2_zeroshot", "b3_dte_style", "b4_vte",
            "b5_narrative_vte"} <= gens
    # Layer-2 (model-level) and cost rows present
    assert any(r["layer"] == "layer2" for r in rows)
    assert any(r["layer"] == "cost" and r["metric"] == "coverage" for r in rows)
    # queue #2: abstention_rate denominator is scoped to abstention-capable
    # generations (B4 + B5), NOT all baselines (else 24/60 reads as 0.08)
    ar = [r for r in rows if r["layer"] == "cost" and r["metric"] == "abstention_rate"]
    n_capable = len({(r["instance_id"], r["grouping"].get("generator_id")) for r in rows
                     if r["layer"] == "layer1"
                     and r["grouping"].get("generator_id") in ("b4_vte", "b5_narrative_vte")})
    assert ar and ar[0]["grouping"].get("scope") == "abstention_capable"
    assert ar[0]["grouping"]["n_denominator"] == n_capable and n_capable > 0
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

    # both prob and margin deltas are emitted (folds the saturation diagnostic in)
    spaces = {r.get("delta_space") for r in rows if r["layer"] == "layer2"}
    assert spaces == {"prob", "margin"}

    # detector competence gate ran on the held-out explanation set and passed
    resolved = yaml.safe_load((run_dir / "config.resolved.yaml").read_text(encoding="utf-8"))
    assert resolved["llm"] == "mistral_7b_instruct"  # llm_id_override honored
    comp = resolved["detector_competence"]
    assert comp["gate_passed"] is True
    assert comp["macro_f1"] >= comp["macro_f1_min"]
    assert set(comp["per_family_recall"]) >= {"BENIGN", "DoS Hulk"}


def test_pilot_replay_rescore_reproduces_metrics_without_provider(tmp_path):
    """A replay re-score serves every generation from the original run's ledger —
    no provider, no tokens — and reproduces the live Layer-1 numbers byte-for-byte
    (this is the mechanism tools/rescore_run.py uses to re-score after Pass B)."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _synthetic_cicids(data_dir / "day1.csv", n=400)

    common = dict(
        data_dir=data_dir, seed=8005, n_explain=40, code_version=CV,
        detector_family="random_forest",
        detector_hyperparameters={"n_estimators": 15, "max_depth": 4, "n_jobs": 1},
        attributor=StubAttributor(), llm_id_override="mistral_7b_instruct",
    )

    live_runs = tmp_path / "runs_live"
    live_dir = run_pilot("EXP-PILOT-001", runs_root=live_runs,
                         llm_provider=DeterministicStubProvider(), **common)

    # Replay against the live run's ledger — no provider passed at all.
    replay_runs = tmp_path / "runs_replay"
    replay_dir = run_pilot("EXP-PILOT-001", runs_root=replay_runs,
                           llm_mode="replay", llm_cache_dir=live_runs / "_pilot_llm_cache",
                           **common)

    assert read_status(replay_dir) is Status.COMPLETE
    resolved = yaml.safe_load((replay_dir / "config.resolved.yaml").read_text(encoding="utf-8"))
    assert resolved["llm_mode"] == "replay"

    def l1(run_id, runs_root):
        return {
            (r["grouping"].get("generator_id"), r["instance_id"], r["metric"]): r["value"]
            for r in load_metrics(run_id, runs_root=runs_root)
            if r["layer"] == "layer1"
        }

    live = l1(live_dir.name, live_runs)
    replay = l1(replay_dir.name, replay_runs)
    assert live and replay == live  # identical Layer-1, produced with no LLM provider


def test_multiclass_run_refuses_to_degenerate_below_three_classes(tmp_path):
    """K<3 guard: this synthetic data holds only BENIGN + DoS, so a multi:*
    objective must fail loudly (naming the rows_per_file remedy) rather than
    silently re-create the trivially separable binary task the K-way detector
    exists to replace. Fires before any trainer/LLM work."""
    import pytest

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _synthetic_cicids(data_dir / "day1.csv", n=400)

    with pytest.raises(ValueError, match="degenerated.*rows_per_file") as exc:
        run_pilot(
            "EXP-PILOT-001",
            data_dir=data_dir,
            runs_root=tmp_path / "runs",
            seed=8005,
            n_explain=40,
            code_version=CV,
            detector_family="random_forest",
            detector_hyperparameters={"objective": "multi:softprob", "n_estimators": 5},
            attributor=StubAttributor(),
            llm_provider=DeterministicStubProvider(),
        )
    assert "BENIGN" in str(exc.value) and "DoS" in str(exc.value)
