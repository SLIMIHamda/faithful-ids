"""Approximate DeepSHAP attributor (L2).

Approximate attributions for the FT-Transformer under an interventional
background sampled from train. Approximate => contributes a bounded, disclosed
ε_att; tolerance-bounded on GPU. ``shap`` and ``torch`` are hard dependencies.

The DeepExplainer wiring depends on the FT-Transformer model (itself a marked
TODO), so ``attribute`` fails loudly until that model exists rather than emitting
fabricated attributions.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import shap  # noqa: F401  (hard dependency; wired in when the FT model lands)
import torch  # noqa: F401

from faithfulids.framework import AttributionArtifact, AttributionMethod


class DeepShapAttributor(AttributionMethod):
    exact = False

    def __init__(self, background_policy: str = "interventional") -> None:
        self.background_policy = background_policy

    def attribute(
        self,
        detector,
        instances: Sequence[Mapping[str, float]],
        instance_ids: Sequence[str],
    ) -> list[AttributionArtifact]:
        raise NotImplementedError(
            "TODO: wire shap.DeepExplainer over the FT-Transformer torch model with "
            "the interventional background sample, and record the background hash in "
            "the cache key. Fails loudly until the FT-Transformer model is implemented "
            "(no fabricated attributions)."
        )


def build(background_policy: str = "interventional", **_: object) -> DeepShapAttributor:
    return DeepShapAttributor(background_policy)
