"""FT-Transformer training entrypoint (L2).

Structure + artifact boundary are in place; the model definition and training
loop are a marked TODO that **fails loudly** rather than emitting an untrained or
fabricated model. ``torch`` is a hard, pinned dependency (no optional-import
fallback). Determinism flags for GPU kernels are recorded in the run manifest;
DeepSHAP over this model is tolerance-bounded (docs/reproducibility-guide.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import torch  # hard dependency; GPU determinism flags set by the runner


def train(
    df: pd.DataFrame,
    *,
    label_column: str,
    hyperparameters: Mapping[str, Any],
    seed: int,
    out_dir: str | Path,
) -> dict[str, Any]:
    """Fit an FT-Transformer and freeze it. (TODO: model + training loop.)"""
    torch.manual_seed(seed)
    raise NotImplementedError(
        "TODO: implement FT-Transformer definition + training loop and freeze the "
        "state dict to models/. Refusing to emit an untrained model — a fabricated "
        "or empty artifact would violate the no-fabrication rule. "
        f"(seed={seed}, out_dir={out_dir}, features={df.shape[1] - 1})"
    )
