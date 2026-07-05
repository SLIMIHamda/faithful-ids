"""ROAR — RemOve-And-Retrain (secondary Layer-2 operator, anchor only) (L4).

ROAR bounds the sensitivity of the Layer-2 conclusions to the erasure-operator
choice by *retraining* the detector on data with the top-k attributed features
removed and measuring the performance drop. Because it retrains, it is expensive
and applied at the anchor only.

The retrain loop is a marked TODO that fails loudly (it must go through the
frozen-artifact training boundary and record its own manifests) rather than
silently approximating — a fabricated ROAR number would misrepresent the
robustness check.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence


def roar_comprehensiveness(
    trainer: Callable[..., Any],
    X,
    y,
    feature_ranking: Sequence[str],
    *,
    k: int,
    seed: int,
) -> float:
    raise NotImplementedError(
        "TODO: implement ROAR — remove the top-k globally-ranked features, retrain "
        "via the detector training entrypoint (new frozen artifact + manifest), and "
        "return the performance drop. Anchor-only secondary operator; fails loudly "
        "rather than approximating."
    )
