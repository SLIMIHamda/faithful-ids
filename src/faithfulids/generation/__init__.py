"""generation — L3, one subpackage per generator.

Generators are dispatched lazily by config ``code`` (``get_generator``); adding
B5 is a new subpackage + config + prompt tree with zero evaluation-code edits.
Generators may not import ``metrics`` (edge 3).
"""

from __future__ import annotations

from faithfulids.generation.base import (
    GENERATOR_MODULES,
    RankedFeature,
    get_generator,
    ranked_feature_list,
    ranked_topk,
)

__all__ = [
    "get_generator",
    "GENERATOR_MODULES",
    "RankedFeature",
    "ranked_topk",
    "ranked_feature_list",
]
