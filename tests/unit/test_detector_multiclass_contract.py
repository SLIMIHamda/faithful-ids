"""Per-class detector contract + the deprecated binary shim (queue #5.2)."""

from __future__ import annotations

import pytest

from faithfulids.detectors.base import FrozenDetector
from faithfulids.framework import attack_probability


def _binary():
    """A binary family that reports ONE attack probability per row (shape (n,))."""
    return FrozenDetector(["a"], lambda m: [0.25 for _ in m])


def _multi():
    """A 3-class family reporting (n, K) already."""
    return FrozenDetector(
        ["a"], lambda m: [[0.5, 0.2, 0.3] for _ in m],
        class_names=["BENIGN", "DoS", "PortScan"],
    )


def test_binary_head_is_normalised_to_per_class_rows():
    det = _binary()
    assert det.class_names == ("BENIGN", "ATTACK")
    out = det.predict_proba([{"a": 1.0}, {"a": 2.0}])
    assert out == [[0.75, 0.25], [0.75, 0.25]]  # [P(BENIGN), P(ATTACK)]


def test_multiclass_shape_and_predicted_class():
    det = _multi()
    assert det.n_classes == 3
    out = det.predict_proba([{"a": 1.0}])
    assert len(out) == 1 and len(out[0]) == 3
    assert det.predicted_class([{"a": 1.0}]) == ["BENIGN"]  # argmax = 0.5


def test_attack_proba_is_exactly_one_minus_p_benign():
    """The shim's semantics are pinned: 1 - P(BENIGN), for ANY number of classes."""
    assert attack_probability(_binary(), [{"a": 1.0}]) == [pytest.approx(0.25)]
    # 3-class: 1 - 0.5 = 0.5 (DoS + PortScan), NOT the argmax probability
    assert attack_probability(_multi(), [{"a": 1.0}]) == [pytest.approx(0.5)]


def test_predict_attack_proba_shim_warns_and_matches_the_helper():
    det = _multi()
    with pytest.warns(DeprecationWarning, match="deprecated binary shim"):
        got = det.predict_attack_proba([{"a": 1.0}])
    assert got == attack_probability(det, [{"a": 1.0}])


def test_attack_proba_requires_a_benign_class():
    det = FrozenDetector(["a"], lambda m: [[0.5, 0.5] for _ in m], class_names=["DoS", "PortScan"])
    with pytest.raises(ValueError, match="BENIGN"):
        attack_probability(det, [{"a": 1.0}])


def test_class_names_must_match_the_probability_width():
    det = FrozenDetector(
        ["a"], lambda m: [[0.5, 0.3, 0.2] for _ in m], class_names=["BENIGN", "DoS"]
    )
    with pytest.raises(ValueError, match="class_names"):
        det.predict_proba([{"a": 1.0}])


def test_multiclass_margin_defers_to_5_4_rather_than_guessing():
    det = FrozenDetector(
        ["a"], lambda m: [[0.5, 0.2, 0.3] for _ in m],
        class_names=["BENIGN", "DoS", "PortScan"],
    )
    with pytest.raises(NotImplementedError, match="5.4"):
        det.predict_margin([{"a": 1.0}])
