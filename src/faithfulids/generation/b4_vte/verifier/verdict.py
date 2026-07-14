"""VtE verifier verdict — FIREWALL SIDE A (L3).

A structured verifier result so B4 can log *why* it (dis)approved a draft, not
just a yes/no. The trace lands in ``ExplanationRecord.metadata['verifier_trace']``
and is the coverage/abstention audit record (queue item #2: b4 metadata was
empty, so abstention triggers — e.g. paraphrase-vs-KB vocabulary — were invisible).

This module holds no evaluation code and imports nothing from ``faithfulids``
(firewall side A stays disjoint from the extractor/metrics).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VerifierVerdict:
    """One verifier decision.

    ``call_id`` is the ledger request hash (LLM verifier) or the verifier's
    ``model_family`` (rule verifier) — kept for LLM-call linkage exactly as the
    old ``(supported, call_id)`` tuple was. ``reason`` is a small stable
    vocabulary describing the decision; ``detail`` carries specifics (e.g. the
    offending feature and its evidence sign on a direction mismatch).
    """

    supported: bool
    call_id: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)

    def as_trace(self, verifier_id: str) -> dict[str, Any]:
        """The metadata record written under ``verifier_trace``."""
        trace: dict[str, Any] = {
            "verifier_id": verifier_id,
            "supported": self.supported,
            "reason": self.reason,
        }
        if self.detail:
            trace["detail"] = dict(self.detail)
        return trace
