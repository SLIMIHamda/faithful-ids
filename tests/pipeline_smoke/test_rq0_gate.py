"""EXP-G-002 end-to-end on the local substitutes: RF detector + stub attributor.

The battery's designated (Layer-1) metrics depend only on claims-vs-attribution,
and B1 constructs claims FROM the attribution, so the gate verdict is
deterministic regardless of detector quality: faithful scores are exact
(mention 1.0, dsa_asserted 1.0, arc 1.0, hfr 0.0) and each operator moves its
designated metric by a fixed amount. The real recorded run uses the K-way
XGBoost on Kaggle; this exercises the identical driver path.
"""

from __future__ import annotations

import json

from faithfulids.orchestration.rq0_gate import run_rq0_gate
from faithfulids.provenance import CodeVersion, Status, read_manifest, read_status

from tests.pipeline_smoke.test_pilot_execute import StubAttributor, _synthetic_cicids

CV = CodeVersion("0" * 40, dirty=False)


def test_rq0_gate_passes_and_records_the_verdict(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _synthetic_cicids(data_dir / "day1.csv", n=400)

    run_dir = run_rq0_gate(
        "EXP-G-002",
        data_dir=data_dir,
        runs_root=tmp_path / "runs",
        n_instances=20,
        code_version=CV,
        detector_id_override="random_forest",
        detector_family="random_forest",
        detector_hyperparameters={"n_estimators": 15, "max_depth": 4, "n_jobs": 1},
        attributor=StubAttributor(),
    )

    assert read_status(run_dir) is Status.COMPLETE
    manifest = read_manifest(run_dir)
    assert manifest.gate == "PASSED"  # deterministic on the designated Layer-1 pairs

    rows = [json.loads(l) for l in open(run_dir / "artifacts" / "metrics.jsonl", encoding="utf-8")]
    verdict = next(r for r in rows if r["metric"] == "gate_verdict")["grouping"]
    assert verdict["passed"] is True
    # magnitude_inflation was REMOVED from the battery (prereg decision
    # 2026-07-18) after the gate run empirically confirmed it undetectable.
    assert verdict["blind_spot_operators"] == []
    assert {"arc", "dsa_asserted", "hfr", "mention_precision", "mention_recall"} <= set(
        verdict["admissible_metrics"]
    )
    # battery rows: 20 instances x (1 faithful + 5 corruptions) per metric
    battery = [r for r in rows if r["layer"] == "rq0" and r["metric"] == "mention_recall"]
    assert len(battery) == 20 * 6
    # designated-pair sensitivities are exact at the recorded operating points
    summ = {r["metric"]: r["grouping"] for r in rows if r["layer"] == "rq0_meta"}
    assert summ["dsa_asserted"]["per_operator_sensitivity"]["sign_flip"] == 1.0
    assert summ["arc"]["per_operator_sensitivity"]["rank_inversion"] == 1.0
    assert summ["mention_recall"]["per_operator_sensitivity"]["omission"] == 1.0
    assert summ["hfr"]["per_operator_sensitivity"]["fabricated_feature"] == 1.0
