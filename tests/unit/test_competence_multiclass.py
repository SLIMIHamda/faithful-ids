"""K-way competence gate + the generation prediction view (queue #5.5)."""

from __future__ import annotations

import pytest

from faithfulids.detectors.competence import (
    evaluate_competence,
    multiclass_classification_table,
)
from faithfulids.orchestration.execute import _prediction_view


class _Multi:
    class_names = ("BENIGN", "DoS", "PortScan")

    def predict_proba(self, rows):
        return [[0.1, 0.7, 0.2] for _ in rows]

    def predicted_class(self, rows):
        return ["DoS" for _ in rows]


class _Binary:
    class_names = ("BENIGN", "ATTACK")

    def predict_proba(self, rows):
        return [[0.2, 0.8], [0.9, 0.1]]

    def predicted_class(self, rows):
        return ["ATTACK", "BENIGN"]


def test_multiclass_recall_is_right_family_not_just_some_attack():
    """A DoS flagged as PortScan is still 'an attack', but the explanation would be
    about the WRONG decision — so K-way recall counts only the right family."""
    table = multiclass_classification_table(
        ["DoS", "DoS", "PortScan", "BENIGN"],
        ["DoS", "PortScan", "PortScan", "BENIGN"],  # one DoS misattributed
    )
    assert table["per_family"]["DoS"]["detection_recall"] == pytest.approx(0.5)
    assert table["per_family"]["PortScan"]["detection_recall"] == pytest.approx(1.0)
    assert table["per_family"]["BENIGN"]["detection_recall"] == pytest.approx(1.0)
    assert table["per_family"]["BENIGN"]["is_attack"] is False
    assert table["auc"] is None  # undefined K-way without a one-vs-rest choice


def test_recall_floor_bites_on_a_blind_family():
    table = multiclass_classification_table(["DoS", "Bot", "Bot"], ["DoS", "DoS", "DoS"])
    comp = evaluate_competence(table, macro_f1_min=0.0, recall_floor=0.8, exemptions=[])
    assert comp.passed is False  # Bot recall = 0.0
    ok = evaluate_competence(table, macro_f1_min=0.0, recall_floor=0.8, exemptions=["Bot"])
    assert ok.passed is True  # ...unless explicitly, loggedly exempted


def test_prediction_view_multiclass_reports_argmax_name_and_its_probability():
    scores, classes = _prediction_view(_Multi(), [{"a": 1.0}])
    assert classes == ["DoS"] and scores == [pytest.approx(0.7)]


def test_prediction_view_binary_strings_are_unchanged():
    """These land in the generation prompt; renaming them would change every LLM
    request hash and break token-free replay of the cached binary runs."""
    scores, classes = _prediction_view(_Binary(), [{"a": 1.0}, {"a": 0.0}])
    assert classes == ["attack", "benign"]
    assert scores == [pytest.approx(0.8), pytest.approx(0.1)]
