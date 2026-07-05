"""The faithfulness error decomposition — definitions only (L0).

The paper's central bookkeeping identity separates *where* an LLM-generated IDS
explanation can be unfaithful:

    ε_model  ≲  ε_nar  +  ε_att

where, for a single explanation of a single detector decision:

* **ε_att (attribution error)** — the gap between the *attribution artifact* and
  the detector's true local behaviour. Exact TreeSHAP over a frozen tree model
  drives ε_att to (near) zero; approximate DeepSHAP admits a bounded, disclosed
  ε_att. This term is a property of the *attribution method*, tagged by
  :attr:`AttributionArtifact.exact`.
* **ε_nar (narration error)** — the gap between the *explanation's claims* and
  the attribution they purport to describe. This is what Layer-1 measures
  (feature-mention P/R/F1, DSA, ARC, HFR over extracted claim tuples). A
  faithful-by-construction generator (B1) has ε_nar ≈ 0 by design.
* **ε_model (model-explanation gap)** — the gap between the explanation's claims
  and the detector's *true* behaviour. This is what Layer-2 (erasure) probes
  directly, without routing through the attribution.

The triangle-style relation ``ε_model ≲ ε_nar + ε_att`` says: an explanation can
only be as faithful to the model as the sum of how faithful the *narration* is
to the attribution and how faithful the *attribution* is to the model. It is why
the paper measures both layers — Layer-1 bounds ε_nar, Layer-2 bounds ε_model,
and their comparison isolates ε_att.

This module provides the *definitions and the bound predicate only*. It computes
nothing from data, holds no thresholds (the slack policy lives in
``configs/``), and imports nothing internal beyond the schema types. Concrete ε
values are produced by the L4 metrics and combined by orchestration.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ErrorComponent(enum.Enum):
    """The three named error terms of the decomposition."""

    MODEL = "eps_model"
    NARRATION = "eps_nar"
    ATTRIBUTION = "eps_att"


@dataclass(frozen=True)
class FaithfulnessDecomposition:
    """A per-explanation decomposition of faithfulness error.

    Each field is a non-negative error magnitude in a shared, metric-defined
    unit (e.g. a normalised disagreement in ``[0, 1]``). The class stores the
    terms and exposes the bound; it does **not** decide whether a given slack is
    scientifically acceptable — that decision is a pre-registered threshold in
    ``configs/statistics/`` and is applied by ``analysis/``.
    """

    eps_nar: float
    eps_att: float
    eps_model: float

    def __post_init__(self) -> None:
        for name in ("eps_nar", "eps_att", "eps_model"):
            v = getattr(self, name)
            if v < 0:
                raise ValueError(f"{name} must be non-negative (got {v})")

    @property
    def bound(self) -> float:
        """The right-hand side ``ε_nar + ε_att``."""
        return self.eps_nar + self.eps_att

    @property
    def residual(self) -> float:
        """``bound - ε_model`` — the slack by which the relation holds.

        A negative residual means the observed ε_model exceeds ε_nar + ε_att, a
        signal that one of the component measurements is mis-calibrated (an RQ0
        concern), not that the identity is false.
        """
        return self.bound - self.eps_model

    def satisfies_bound(self, slack: float = 0.0) -> bool:
        """Whether ``ε_model ≤ ε_nar + ε_att + slack``.

        ``slack`` is supplied by the caller from a pre-registered config; this
        method embeds no numeric policy of its own.
        """
        if slack < 0:
            raise ValueError("slack must be non-negative")
        return self.eps_model <= self.bound + slack
