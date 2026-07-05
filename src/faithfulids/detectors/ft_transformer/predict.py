"""FT-Transformer inference (L2). Loads a frozen artifact ONLY (edge 6).

Loading is a marked TODO that fails loudly until training is implemented — it
never returns a stand-in model.
"""

from __future__ import annotations

from pathlib import Path

import torch  # hard dependency

from faithfulids.detectors.base import FrozenDetector


def load(model_dir: str | Path) -> FrozenDetector:
    raise NotImplementedError(
        "TODO: reconstruct the FT-Transformer from the frozen state dict in "
        f"{model_dir} and wrap it as a FrozenDetector. No frozen artifact exists "
        "until train.py is implemented (fails loudly rather than faking one). "
        f"(torch {torch.__version__ if hasattr(torch, '__version__') else '?'})"
    )
