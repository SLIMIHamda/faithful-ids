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

from faithfulids.attribution.base import select_predicted_class_shap
from faithfulids.framework import AttributionArtifact, AttributionMethod


def _is_per_class(values) -> bool:
    """True when SHAP returned one attribution PER CLASS (multi-class model):
    a list of >1 arrays, or a single ``(n, F, K)`` array."""
    if isinstance(values, list):
        return len(values) > 1
    return np.ndim(values) == 3


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

        if _is_per_class(values):
            # MULTI-CLASS (queue #5.3): one attribution per class — explain the class
            # the detector actually PREDICTED, not an arbitrary column (the old
            # values[-1] would have silently explained the last class).
            class_names = tuple(getattr(detector, "class_names", ()) or ())
            if not class_names:
                raise ValueError(
                    "multi-class TreeSHAP needs detector.class_names to know which "
                    "SHAP column each class is (queue #5.2 contract)."
                )
            predicted = list(detector.predicted_class(instances))
            class_index = [class_names.index(name) for name in predicted]
            selected, base_per_instance = select_predicted_class_shap(values, base, class_index)
            explained = predicted  # provenance: per-instance, the class explained
        else:
            # BINARY / single-output: SHAP explains the positive (attack) side, which
            # is this pilot's established semantics for every instance — benign rows
            # included (the benign attribution is just its negation). Unchanged.
            if isinstance(values, list):
                values = values[-1]
            selected = np.asarray(values, dtype=float)
            b = float(np.ravel(base)[-1]) if np.ndim(base) else float(base)
            base_per_instance = [b] * len(instance_ids)
            # the positive class (last column) is what a binary head's SHAP explains
            names = tuple(getattr(detector, "class_names", ()) or ())
            explained = [names[-1] if names else "ATTACK"] * len(instance_ids)

        artifacts: list[AttributionArtifact] = []
        for i, iid in enumerate(instance_ids):
            artifacts.append(
                AttributionArtifact(
                    instance_id=iid,
                    feature_names=tuple(feature_names),
                    values=tuple(float(v) for v in np.ravel(selected[i])),
                    base_value=float(base_per_instance[i]),
                    method="treeshap",
                    exact=True,
                    background_policy=self.background_policy,
                    explained_class=explained[i],
                )
            )
        return artifacts


def build(background_policy: str = "tree_path_dependent", **_: object) -> TreeShapAttributor:
    return TreeShapAttributor(background_policy)
