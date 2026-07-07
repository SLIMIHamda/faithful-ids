"""Detector competence: per-family recall table + the imbalance-aware gate."""

from __future__ import annotations

import pytest

from faithfulids.detectors.competence import classification_table, evaluate_competence


def test_classification_table_per_family_recall():
    # 3 benign (all correct), 2 DoS (both detected), 2 Infiltration (1 missed).
    families = ["BENIGN", "BENIGN", "BENIGN", "DoS Hulk", "DoS Hulk", "Infiltration", "Infiltration"]
    y_true = [0, 0, 0, 1, 1, 1, 1]
    y_pred = [0, 0, 0, 1, 1, 1, 0]
    t = classification_table(y_true, y_pred, families, y_score=[0.1, 0.2, 0.1, 0.9, 0.8, 0.7, 0.4])
    assert t["per_family"]["BENIGN"]["detection_recall"] == pytest.approx(1.0)
    assert t["per_family"]["DoS Hulk"]["detection_recall"] == pytest.approx(1.0)
    assert t["per_family"]["Infiltration"]["detection_recall"] == pytest.approx(0.5)
    assert t["per_family"]["Infiltration"]["support"] == 2
    assert t["confusion"] == {"tn": 3, "fp": 0, "fn": 1, "tp": 3}
    assert 0.0 <= t["macro_f1"] <= 1.0


def test_gate_fails_when_a_rare_family_is_blind():
    families = ["BENIGN"] * 4 + ["Infiltration"] * 4
    y_true = [0, 0, 0, 0, 1, 1, 1, 1]
    y_pred = [0, 0, 0, 0, 0, 0, 0, 1]  # Infiltration recall = 0.25 — a blind spot
    t = classification_table(y_true, y_pred, families)
    r = evaluate_competence(t, macro_f1_min=0.5, recall_floor=0.8, exemptions=())
    assert not r.passed
    assert any(fam == "Infiltration" for fam, _ in r.failures)


def test_gate_exemption_allows_untrainable_family():
    families = ["BENIGN"] * 4 + ["Infiltration"] * 4
    y_true = [0, 0, 0, 0, 1, 1, 1, 1]
    y_pred = [0, 0, 0, 0, 0, 0, 0, 1]
    t = classification_table(y_true, y_pred, families)
    r = evaluate_competence(t, macro_f1_min=0.0, recall_floor=0.8, exemptions=["Infiltration"])
    assert r.passed
    assert r.exemptions == ("Infiltration",)


def test_gate_fails_on_low_macro_f1_even_when_attack_recall_is_perfect():
    # Predict everything attack: attack recall is perfect, but benign is destroyed
    # -> macro-F1 collapses. The aggregate-looking-fine trap the gate exists for.
    families = ["BENIGN"] * 5 + ["DoS Hulk"] * 5
    y_true = [0] * 5 + [1] * 5
    y_pred = [1] * 10
    t = classification_table(y_true, y_pred, families)
    assert t["per_family"]["DoS Hulk"]["detection_recall"] == pytest.approx(1.0)
    r = evaluate_competence(t, macro_f1_min=0.9, recall_floor=0.8)
    assert not r.passed  # macro-F1 well below 0.9
