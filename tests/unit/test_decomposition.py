"""The ε_model ≲ ε_nar + ε_att decomposition (definitions)."""

from __future__ import annotations

import pytest

from faithfulids.framework import FaithfulnessDecomposition


def test_bound_and_residual():
    d = FaithfulnessDecomposition(eps_nar=0.2, eps_att=0.1, eps_model=0.25)
    assert d.bound == pytest.approx(0.3)
    assert d.residual == pytest.approx(0.05)
    assert d.satisfies_bound()


def test_bound_violation_signalled_by_negative_residual():
    d = FaithfulnessDecomposition(eps_nar=0.05, eps_att=0.05, eps_model=0.4)
    assert d.residual < 0
    assert not d.satisfies_bound()
    assert d.satisfies_bound(slack=0.31)


def test_negative_components_rejected():
    with pytest.raises(ValueError):
        FaithfulnessDecomposition(eps_nar=-0.1, eps_att=0.0, eps_model=0.0)


def test_negative_slack_rejected():
    d = FaithfulnessDecomposition(0.1, 0.1, 0.1)
    with pytest.raises(ValueError):
        d.satisfies_bound(slack=-0.01)
