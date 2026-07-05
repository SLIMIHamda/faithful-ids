"""VtE abstention policy (L3).

On an unsupported verdict the generator abstains and its output degrades to the
faithful-by-construction B1 template — **never silence** (blueprint §8 rule 3).
Abstention is reported downstream as a coverage–risk curve, which is a mandatory
output of every B4 cell.
"""

from __future__ import annotations


def decide_abstention(supported: bool) -> bool:
    """Abstain iff the draft was not verified as supported."""
    return not supported
