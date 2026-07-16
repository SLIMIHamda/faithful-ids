"""Predicted-class SHAP selection (queue #5.3).

The multi-class selection core is pure + numpy-only so it is testable offline:
``shap`` is a Kaggle-only dependency, so ``attribution.treeshap`` cannot even be
imported here — ``attribution.base`` stays lazy and holds the logic.
"""

from __future__ import annotations

import numpy as np
import pytest

from faithfulids.attribution.base import select_predicted_class_shap

# 3 classes, 2 instances, 2 features. Class k's values are all k.<instance> so the
# selected class is unambiguous in the assertions.
_LIST_FORM = [
    np.array([[0.0, 0.1], [0.2, 0.3]]),   # class 0
    np.array([[1.0, 1.1], [1.2, 1.3]]),   # class 1
    np.array([[2.0, 2.1], [2.2, 2.3]]),   # class 2
]
_BASE = [10.0, 20.0, 30.0]


def test_selects_each_instances_predicted_class_from_list_form():
    vals, base = select_predicted_class_shap(_LIST_FORM, _BASE, [2, 0])
    # instance 0 predicted class 2 -> class-2 row 0 ; instance 1 predicted 0 -> class-0 row 1
    assert vals.tolist() == [[2.0, 2.1], [0.2, 0.3]]
    assert base.tolist() == [30.0, 10.0]


def test_equivalent_for_the_n_f_k_array_form():
    arr = np.stack(_LIST_FORM, axis=2)  # (n, F, K)
    assert arr.shape == (2, 2, 3)
    vals, base = select_predicted_class_shap(arr, _BASE, [2, 0])
    assert vals.tolist() == [[2.0, 2.1], [0.2, 0.3]]
    assert base.tolist() == [30.0, 10.0]


def test_scalar_base_is_broadcast():
    vals, base = select_predicted_class_shap(_LIST_FORM, 7.0, [1, 1])
    assert vals.tolist() == [[1.0, 1.1], [1.2, 1.3]]
    assert base.tolist() == [7.0, 7.0]


def test_rejects_class_index_length_mismatch():
    with pytest.raises(ValueError, match="class_index"):
        select_predicted_class_shap(_LIST_FORM, _BASE, [0])  # 1 index, 2 instances


def test_rejects_out_of_range_class_index():
    with pytest.raises(ValueError, match="out of range"):
        select_predicted_class_shap(_LIST_FORM, _BASE, [3, 0])


def test_rejects_non_per_class_array():
    with pytest.raises(ValueError, match="per-class SHAP"):
        select_predicted_class_shap(np.array([[0.0, 1.0], [2.0, 3.0]]), _BASE, [0, 1])
