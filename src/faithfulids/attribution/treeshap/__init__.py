"""Exact TreeSHAP attributor (L2).

Exact Shapley values over frozen tree ensembles (XGBoost booster / RF). Exact =>
the ε_att term is (near) zero. Consumes the tree model via ``detector.native_model``
(duck-typed — attribution must NOT import ``detectors``: they are independent L2
siblings). ``shap`` is a hard, pinned dependency.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import shap

from faithfulids.framework import AttributionArtifact, AttributionMethod


class TreeShapAttributor(AttributionMethod):
    exact = True

    def __init__(self, background_policy: str = "tree_path_dependent") -> None:
        self.background_policy = background_policy

    def attribute(
        self,
        detector,
        instances: Sequence[Mapping[str, float]],
        instance_ids: Sequence[str],
    ) -> list[AttributionArtifact]:
        model = getattr(detector, "native_model", None)
        if model is None:
            raise ValueError(
                "TreeSHAP requires the underlying tree model (detector.native_model)."
            )
        feature_names = list(detector.feature_names)
        X = np.array(
            [[float(row[f]) for f in feature_names] for row in instances], dtype=float
        )
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(X)
        base = explainer.expected_value

        # Normalise binary-classifier outputs to the positive class.
        if isinstance(values, list):
            values = values[-1]
        base_value = float(np.ravel(base)[-1]) if np.ndim(base) else float(base)

        artifacts: list[AttributionArtifact] = []
        for i, iid in enumerate(instance_ids):
            artifacts.append(
                AttributionArtifact(
                    instance_id=iid,
                    feature_names=tuple(feature_names),
                    values=tuple(float(v) for v in np.ravel(values[i])),
                    base_value=base_value,
                    method="treeshap",
                    exact=True,
                    background_policy=self.background_policy,
                )
            )
        return artifacts


def build(background_policy: str = "tree_path_dependent", **_: object) -> TreeShapAttributor:
    return TreeShapAttributor(background_policy)
