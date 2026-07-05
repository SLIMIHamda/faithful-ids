"""Erasure operators for Layer-2 (L4).

The erasure background is deliberately NOT the SHAP baseline distribution.
Primary operator = conditional-expectation imputation (per-class kNN / light
generative model); the fitted imputation model is a manifested cache artifact
with its own seed + data hash (hostile-audit A11). ``SimpleBackgroundErasure``
is a deterministic reference operator used by fixtures.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np


class SimpleBackgroundErasure:
    """Replace erased features with fixed background values (deterministic)."""

    def __init__(self, background: Mapping[str, float]) -> None:
        self._bg = dict(background)

    def erase(
        self, instance: Mapping[str, float], features_to_remove: Sequence[str]
    ) -> dict[str, float]:
        out = dict(instance)
        for f in features_to_remove:
            out[f] = float(self._bg.get(f, 0.0))
        return out


class ConditionalExpectationImputer:
    """E[X_removed | X_retained] via kNN over the retained features.

    Fitted on the training matrix; ``erase`` imputes the removed features with
    the mean of the k nearest neighbours in retained-feature space. A per-class
    variant conditions additionally on the class (supplied by the harness); this
    global form is the class-agnostic conditional expectation.
    """

    def __init__(self, k: int = 5) -> None:
        self.k = k
        self._X: np.ndarray | None = None
        self._feature_names: list[str] = []

    def fit(self, X, feature_names: Sequence[str]) -> "ConditionalExpectationImputer":
        self._X = np.asarray(X, dtype=float)
        self._feature_names = list(feature_names)
        return self

    def erase(
        self, instance: Mapping[str, float], features_to_remove: Sequence[str]
    ) -> dict[str, float]:
        if self._X is None:
            raise RuntimeError("ConditionalExpectationImputer must be fit before use")
        from sklearn.neighbors import NearestNeighbors

        remove = set(features_to_remove)
        retained = [f for f in self._feature_names if f not in remove]
        out = dict(instance)
        if not retained:  # nothing to condition on -> global mean
            means = self._X.mean(axis=0)
            for f in features_to_remove:
                out[f] = float(means[self._feature_names.index(f)])
            return out
        ret_idx = [self._feature_names.index(f) for f in retained]
        query = np.array([[instance[f] for f in retained]], dtype=float)
        n_neighbors = min(self.k, len(self._X))
        nn = NearestNeighbors(n_neighbors=n_neighbors).fit(self._X[:, ret_idx])
        _, idx = nn.kneighbors(query)
        neigh = self._X[idx[0]]
        for f in features_to_remove:
            j = self._feature_names.index(f)
            out[f] = float(neigh[:, j].mean())
        return out
