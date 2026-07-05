"""extraction — L3, FIREWALL SIDE B.

The evaluation claim extractor. No imports from ``generation.*`` (edge 2a); own
prompt tree and model family, disjoint from the VtE verifier (side A).
"""

from __future__ import annotations

from faithfulids.extraction.extractor import RuleAssistedExtractor, build

__all__ = ["RuleAssistedExtractor", "build"]
