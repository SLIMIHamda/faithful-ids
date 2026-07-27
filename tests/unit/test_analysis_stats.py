"""Statistical pipelines (analysis boundary A) — pure consumers, tested in isolation."""

from __future__ import annotations

import numpy as np
import pytest

from analysis.src.bootstrap_ci import bootstrap_mean_ci, cohens_d
from analysis.src.coverage_risk import risk_coverage_curve
from analysis.src.friedman_nemenyi import average_ranks, friedman_nemenyi
from analysis.src.variance_components import variance_shares
from analysis.src.wilcoxon_pairs import holm_bonferroni, wilcoxon_pair


def test_friedman_nemenyi_ranks_best_method_first():
    scores = [
        [0.90, 0.80, 0.85, 0.88, 0.86],  # method 0 always best
        [0.10, 0.20, 0.15, 0.05, 0.12],
        [0.30, 0.25, 0.20, 0.35, 0.28],
    ]
    res = friedman_nemenyi(scores, higher_is_better=True)
    assert res["n_methods"] == 3 and res["n_blocks"] == 5
    assert res["avg_ranks"][0] == min(res["avg_ranks"])
    assert res["pvalue"] < 0.05
    assert res["critical_difference"] > 0


def test_average_ranks_simple():
    r = average_ranks(np.array([[1.0, 1.0], [0.0, 0.0]]), higher_is_better=True)
    assert r[0] == 1.0 and r[1] == 2.0


def test_wilcoxon_and_holm_monotone():
    w = wilcoxon_pair([0.9, 0.8, 0.85, 0.7, 0.75], [0.1, 0.2, 0.15, 0.3, 0.25])
    assert 0.0 <= w["pvalue"] <= 1.0
    adj = holm_bonferroni({"h1": 0.01, "h2": 0.04, "h3": 0.5})
    assert adj["h1"] <= adj["h2"] <= adj["h3"]
    assert adj["h1"] == pytest.approx(0.03)


def test_bootstrap_ci_brackets_mean_and_is_reproducible():
    vals = [0.5, 0.6, 0.55, 0.52, 0.58]
    ci = bootstrap_mean_ci(vals, n_resamples=2000, seed=0)
    assert ci["ci_low"] <= ci["mean"] <= ci["ci_high"]
    assert ci == bootstrap_mean_ci(vals, n_resamples=2000, seed=0)  # seeded


def test_cohens_d_sign():
    # differences vary (non-zero variance) and are positive on average
    assert cohens_d([1.0, 2.0, 3.0, 4.0], [0.0, 1.5, 2.0, 3.0]) > 0


def test_coverage_risk_curve_is_monotone_in_coverage():
    res = risk_coverage_curve([0.0, 1.0, 0.0, 1.0], [0.9, 0.1, 0.8, 0.2])
    assert res["coverage"] == sorted(res["coverage"])
    assert res["aurc"] >= 0.0


def _row(inst, metric, value, gen="b4_vte"):
    return {"instance_id": inst, "layer": "layer1", "metric": metric,
            "value": value, "grouping": {"generator_id": gen}}


def test_gated_instance_values_excludes_undefined_but_keeps_failures():
    """NaN-exclusion aggregation: dsa_asserted gated on direction_assertion_rate
    drops no-assertion instances (structural 0.0) but KEEPS a genuinely-wrong
    asserted instance (rate>0, value 0.0) — real failures must not be hidden."""
    from analysis.run import _instance_values

    rows = [
        _row("i0", "dsa_asserted", 1.0), _row("i0", "direction_assertion_rate", 1.0),  # asserted, correct
        _row("i1", "dsa_asserted", 0.0), _row("i1", "direction_assertion_rate", 1.0),  # asserted, WRONG -> keep
        _row("i2", "dsa_asserted", 0.0), _row("i2", "direction_assertion_rate", 0.0),  # silent -> drop
    ]
    gated = _instance_values(rows, "dsa_asserted", "b4_vte", gate_metric="direction_assertion_rate")
    ungated = _instance_values(rows, "dsa_asserted", "b4_vte")
    assert gated == [1.0, 0.0]  # i2 dropped, i1 (real failure) kept
    assert sum(gated) / len(gated) == pytest.approx(0.5)
    assert ungated == [1.0, 0.0, 0.0]  # naive mean would be 0.333 — the structural-zero trap


def test_gated_instance_values_arc_pairs_threshold():
    """ARC gated on arc_n_pairs>=2 (Spearman needs >=2 points): drops <2-pair
    instances (structural 0.0) but keeps a genuine anti-correlation (pairs>=2)."""
    from analysis.run import _instance_values

    rows = [
        _row("i0", "arc", 1.0), _row("i0", "arc_n_pairs", 3.0),    # defined, kept
        _row("i1", "arc", -1.0), _row("i1", "arc_n_pairs", 2.0),   # anti-corr FAILURE -> keep
        _row("i2", "arc", 0.0), _row("i2", "arc_n_pairs", 1.0),    # < 2 pairs -> undefined -> drop
    ]
    gated = _instance_values(rows, "arc", "b4_vte", gate_metric="arc_n_pairs", gate_min=2)
    assert gated == [1.0, -1.0]  # i2 dropped; the real failure i1 stays in


def test_capability_points_join_and_pending():
    """Capability anchor join: sorts by params, joins by llm, and stays 'pending'
    (capability_populated False) while any MMLU is null — never fabricates an x-axis."""
    from analysis.run import _capability_points, _mean

    assert _mean([]) is None and _mean([1.0, 2.0]) == 1.5
    anchor = [
        {"llm": "big", "params_b": 32.0, "mmlu": None, "ifeval": None},
        {"llm": "small", "params_b": 3.0, "mmlu": 0.60, "ifeval": 0.50},
    ]
    summaries = [
        {"llm": "big", "faithfulness": {"b2_zeroshot": 0.10}},
        {"llm": "small", "faithfulness": {"b2_zeroshot": 0.06}},
    ]
    res = _capability_points(anchor, summaries, "mention_f1", ["b2_zeroshot"])
    assert [p["llm"] for p in res["points"]] == ["small", "big"]  # sorted by params_b
    assert res["capability_populated"] is False  # big.mmlu is null
    # once every model's MMLU is filled, it becomes plottable
    anchor[0]["mmlu"] = 0.80
    res2 = _capability_points(anchor, summaries, "mention_f1", ["b2_zeroshot"])
    assert res2["capability_populated"] is True
    assert res2["points"][1] == {"llm": "big", "params_b": 32.0, "mmlu": 0.80,
                                 "ifeval": None, "faithfulness": {"b2_zeroshot": 0.10}}


def test_variance_shares_bounded():
    sh = variance_shares([1, 2, 3, 4, 5, 6], {"g": ["a", "a", "a", "b", "b", "b"]})
    assert 0.0 <= sh["g"] <= 1.0
    assert "residual" in sh


def test_mixed_extractor_versions_cannot_be_aggregated(monkeypatch):
    """Layer-1 metrics are computed over extracted claims, so aggregating runs
    scored by different extractors compares instrument behaviour and generator
    behaviour at once. Previously this was discipline ('re-score first'); it is
    now a precondition that names both versions."""
    from faithfulids.results.api import ResultError

    import analysis.run as ar

    versions = {"run-a": "1.4.0", "run-b": "1.2.0"}
    monkeypatch.setattr(ar, "run_extractor_version", lambda rid, root=None: versions[rid])
    with pytest.raises(ResultError) as exc:
        ar.assert_single_extractor_version(["run-a", "run-b"])
    assert "1.4.0" in str(exc.value) and "1.2.0" in str(exc.value)
    assert "rescore_run" in str(exc.value)


def test_matched_extractor_versions_aggregate_and_report_the_version(monkeypatch):
    import analysis.run as ar

    monkeypatch.setattr(ar, "run_extractor_version", lambda rid, root=None: "1.4.0")
    assert ar.assert_single_extractor_version(["run-a", "run-b"]) == "1.4.0"
    # a run set with no claims at all makes no version claim
    monkeypatch.setattr(ar, "run_extractor_version", lambda rid, root=None: None)
    assert ar.assert_single_extractor_version(["run-a"]) is None


def test_an_unknown_version_beside_a_known_one_is_a_mismatch(monkeypatch):
    """A run whose claims are missing cannot be certified as instrument-matched,
    so it must not pass silently next to a run that is."""
    from faithfulids.results.api import ResultError

    import analysis.run as ar

    versions = {"run-a": "1.4.0", "run-b": None}
    monkeypatch.setattr(ar, "run_extractor_version", lambda rid, root=None: versions[rid])
    with pytest.raises(ResultError):
        ar.assert_single_extractor_version(["run-a", "run-b"])


def test_layer2_per_class_groups_by_predicted_class_in_both_spaces(tmp_path, monkeypatch):
    """Per-class Layer-2 breakdown (amendment 0002): eps_att comprehensiveness@3
    split by grouping.predicted_class, prob AND margin. Binary rows (no
    predicted_class) contribute nothing."""
    import analysis.run as ar

    rows = []
    def add(space, cls, val):
        rows.append({"layer": "layer2", "metric": "comprehensiveness",
                     "component": "eps_att", "delta_space": space, "k": 3,
                     "value": val, "instance_id": "i",
                     "grouping": ({"predicted_class": cls} if cls else {})})
    # DDoS saturated in prob (0.0), signal in margin; Bot the opposite
    add("prob", "DDoS", 0.0); add("prob", "DDoS", 0.0); add("prob", "Bot", 0.8)
    add("margin", "DDoS", 3.0); add("margin", "Bot", 9.0)
    add("prob", None, 0.5)  # a binary row -> excluded from per-class

    monkeypatch.setattr(ar, "load_config", lambda name: {
        "id": "t", "test": "layer2_per_class", "metric": "comprehensiveness",
        "component": "eps_att", "k": 3, "delta_spaces": ["prob", "margin"],
        "run_ids": ["r"],
    })
    monkeypatch.setattr(ar, "load_metrics", lambda rid, root=None: rows)
    monkeypatch.setattr(ar, "run_extractor_version", lambda rid, root=None: "1.4.0")

    payload, _ = ar.build_result("t")
    res = payload["result"]["by_delta_space"]
    assert res["prob"]["per_class"]["DDoS"] == 0.0
    assert res["prob"]["per_class"]["Bot"] == 0.8
    assert res["prob"]["n_per_class"] == {"Bot": 1, "DDoS": 2}
    assert "None" not in res["prob"]["per_class"] and None not in res["prob"]["per_class"]
    assert res["margin"]["per_class"]["Bot"] == 9.0
    # the aggregate the breakdown exists to caveat
    assert res["prob"]["aggregate"] == (0.0 + 0.0 + 0.8) / 3


def test_redundancy_2x2_separates_redundant_from_irrelevant():
    """Prereg amendment 0003. comprehensiveness HIGH is good, sufficiency LOW is
    good, and the pair fails in OPPOSITE directions under correlation — which is
    the only way to tell a cited set whose signal a correlated substitute carries
    (redundant) from one that carries nothing (irrelevant). Both look identical
    on comprehensiveness alone."""
    from analysis.src.redundancy import CELLS, classify, tabulate

    thr = 0.10
    assert classify(0.02, 0.01, thr) == "redundant"              # erasing does nothing, keeping suffices
    assert classify(0.02, 0.90, thr) == "irrelevant"             # erasing does nothing, keeping does nothing
    assert classify(0.80, 0.01, thr) == "load_bearing"           # necessary AND sufficient
    assert classify(0.80, 0.90, thr) == "necessary_not_sufficient"
    # the boundary is >= on both axes, fixed so it cannot follow a result
    assert classify(thr, 0.0, thr) == "load_bearing"
    assert classify(thr - 1e-9, 0.0, thr) == "redundant"

    table = tabulate(
        [
            {"comprehensiveness": 0.0, "sufficiency": 0.0, "predicted_class": "BENIGN"},
            {"comprehensiveness": 0.0, "sufficiency": 0.0, "predicted_class": "BENIGN"},
            {"comprehensiveness": 0.5, "sufficiency": 0.0, "predicted_class": "Bot"},
            {"comprehensiveness": 0.0, "sufficiency": 0.5, "predicted_class": None},
        ],
        threshold=thr,
    )
    assert table["n"] == 4
    assert table["counts"] == {"redundant": 2, "load_bearing": 1,
                               "irrelevant": 1, "necessary_not_sufficient": 0}
    assert set(table["counts"]) == set(CELLS)
    assert table["fractions"]["redundant"] == 0.5
    # every BENIGN instance redundant -> prob-space ~0 there is redundancy, not
    # attribution failure; the None-class row counts in the total but names no class
    assert table["by"]["predicted_class"]["BENIGN"]["redundant"] == 2
    assert "None" not in table["by"]["predicted_class"]
    assert "generator_id" not in table["by"]  # eps_att is generator-blind


def test_layer2_redundancy_pairs_the_two_metrics_and_reports_the_operator(monkeypatch):
    """The analysis test pairs comprehensiveness with sufficiency per instance at
    one k/space, and echoes the removal operator R the numbers are conditional
    on — no Layer-2 table is readable without it (amendment 0003)."""
    import analysis.run as ar

    rows = []
    def add(metric, space, inst, cls, val):
        rows.append({"layer": "layer2", "metric": metric, "component": "eps_att",
                     "delta_space": space, "k": 3, "value": val,
                     "instance_id": inst, "grouping": {"predicted_class": cls}})
    # i1: erasing does nothing AND keeping suffices -> redundant (the BENIGN case)
    add("comprehensiveness", "prob", "i1", "BENIGN", 0.00)
    add("sufficiency", "prob", "i1", "BENIGN", 0.01)
    # i2: erasing bites -> load-bearing
    add("comprehensiveness", "prob", "i2", "Bot", 0.60)
    add("sufficiency", "prob", "i2", "Bot", 0.02)
    # margin un-saturates i1: same instance reads load-bearing there
    add("comprehensiveness", "margin", "i1", "BENIGN", 4.00)
    add("sufficiency", "margin", "i1", "BENIGN", 0.01)
    add("comprehensiveness", "margin", "i2", "Bot", 7.00)
    add("sufficiency", "margin", "i2", "Bot", 0.02)
    # an unpaired comprehensiveness at a different k must not be classified
    rows.append({"layer": "layer2", "metric": "comprehensiveness", "component": "eps_att",
                 "delta_space": "prob", "k": 5, "value": 0.9,
                 "instance_id": "i3", "grouping": {"predicted_class": "DDoS"}})

    monkeypatch.setattr(ar, "load_config", lambda name: {
        "id": "t", "test": "layer2_redundancy", "component": "eps_att",
        "metric_pair": ["comprehensiveness", "sufficiency"], "k": 3,
        "threshold": 0.10, "delta_spaces": ["prob", "margin"], "run_ids": ["r"],
    })
    monkeypatch.setattr(ar, "load_metrics", lambda rid, root=None: rows)
    monkeypatch.setattr(ar, "run_extractor_version", lambda rid, root=None: "1.4.0")
    monkeypatch.setattr(ar, "run_resolved_config",
                        lambda rid, root=None: {"layer2_erasure_operator": "conditional"})

    payload, _ = ar.build_result("t")
    res = payload["result"]
    assert res["erasure_operators"] == ["conditional"]
    prob, margin = res["by_delta_space"]["prob"], res["by_delta_space"]["margin"]
    assert prob["n"] == 2  # the k=5 row has no sufficiency partner -> dropped
    assert prob["counts"]["redundant"] == 1 and prob["counts"]["load_bearing"] == 1
    assert prob["by"]["predicted_class"]["BENIGN"]["redundant"] == 1
    # the finding amendment 0002 rests on: prob calls BENIGN redundant, margin
    # calls the same instance load-bearing
    assert margin["counts"]["load_bearing"] == 2
