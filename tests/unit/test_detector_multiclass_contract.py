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


def test_binary_margin_is_per_class_and_antisymmetric():
    """(queue #5.4) predict_margin mirrors predict_proba's (n,K). A binary head's
    single attack margin m yields [-m, m] — logit(P(BENIGN)) = -logit(P(ATTACK))."""
    det = FrozenDetector(["a"], lambda m: [0.25 for _ in m], margin=lambda m: [1.5 for _ in m])
    assert det.predict_margin([{"a": 1.0}]) == [[-1.5, 1.5]]


def test_multiclass_margin_uses_the_native_per_class_margin():
    det = FrozenDetector(
        ["a"], lambda m: [[0.5, 0.2, 0.3] for _ in m],
        class_names=["BENIGN", "DoS", "PortScan"],
        margin=lambda m: [[0.1, -0.2, 0.3] for _ in m],
    )
    assert det.predict_margin([{"a": 1.0}]) == [[0.1, -0.2, 0.3]]


def test_multiclass_margin_without_a_native_margin_fails_loudly():
    det = FrozenDetector(
        ["a"], lambda m: [[0.5, 0.2, 0.3] for _ in m],
        class_names=["BENIGN", "DoS", "PortScan"],
    )
    with pytest.raises(NotImplementedError, match="native per-class margin"):
        det.predict_margin([{"a": 1.0}])


def test_random_forest_multiclass_freezes_class_names_and_log_prob_margin(tmp_path):
    """Tier-A detector axis (EXP-A-002/004): sklearn RF trained on target_index
    freezes class_names with the model and exposes a per-class log-probability
    margin (documented: log(clip(P_k)), not log-odds) so margin-space Layer-2
    stays defined on this family."""
    import numpy as np
    import pandas as pd

    from faithfulids.detectors.base import load_frozen
    from faithfulids.detectors.random_forest.train import train

    rng = np.random.RandomState(0)
    n = 300
    y = np.arange(n) % 3
    df = pd.DataFrame({
        "f1": y * 2.0 + rng.rand(n) * 0.1,   # cleanly separable by class
        "f2": rng.rand(n),
        "target_index": y,
    })
    names = ["BENIGN", "DoS", "PortScan"]
    metrics = train(df, label_column="target_index",
                    hyperparameters={"n_estimators": 10, "n_jobs": 1},
                    seed=0, out_dir=tmp_path, class_names=names)
    assert metrics["n_classes"] == 3 and metrics["class_names"] == names
    assert metrics["train_auc"] is None  # AUC undefined K-way

    det = load_frozen("random_forest", tmp_path)
    assert det.class_names == tuple(names)
    rows = [{"f1": 2.0, "f2": 0.5}, {"f1": 0.0, "f2": 0.5}]
    proba = det.predict_proba(rows)
    assert len(proba[0]) == 3
    assert det.predicted_class(rows) == ["DoS", "BENIGN"]
    margin = det.predict_margin(rows)
    expect = np.log(np.clip(np.asarray(proba, dtype=float), 1e-12, 1.0))
    assert np.allclose(np.asarray(margin), expect)


def test_random_forest_rejects_sparse_target_indices(tmp_path):
    import pandas as pd
    import pytest

    from faithfulids.detectors.random_forest.train import train

    df = pd.DataFrame({"f1": [0.1, 0.9, 0.2, 0.8], "target_index": [0, 2, 0, 2]})  # no class 1
    with pytest.raises(ValueError, match="0..K-1"):
        train(df, label_column="target_index",
              hyperparameters={"n_estimators": 5, "n_jobs": 1},
              seed=0, out_dir=tmp_path, class_names=["A", "B", "C"])
