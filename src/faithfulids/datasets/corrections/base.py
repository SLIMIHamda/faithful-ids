"""Deterministic, versioned correction transforms (L1).

The corrected-CICIDS2017 pipeline is itself a reviewable scientific claim
(hostile-audit A3): it must be deterministic, tested, and record the exact
fix-set applied. Each fix is a :class:`CorrectionRule` with a name + version.

**Unimplemented fixes hard-fail.** A rule whose logic is not yet implemented
raises :class:`UnimplementedCorrection` when executed — it never silently passes
data through, because a silent pass-through would fabricate a "corrected"
dataset that is really the raw one (coding-standards: stubs fail loudly).
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd


class UnimplementedCorrection(NotImplementedError):
    """Raised when an unimplemented correction rule is executed."""


class CorrectionRule(abc.ABC):
    """One deterministic correction step over a dataframe."""

    #: stable rule name, recorded in CORRECTIONS_APPLIED.md
    name: str
    #: rule semver, bumped when the fix logic changes (=> a new corrected corpus)
    version: str

    @abc.abstractmethod
    def apply(self, df: "pd.DataFrame") -> "pd.DataFrame":
        """Return a corrected copy of ``df``. Must be deterministic and pure."""


class TodoCorrection(CorrectionRule):
    """A registered-but-unimplemented fix. Executing it fails loudly.

    Used to encode the Engelen/Lanvin fix-set structure before each rule's exact
    logic is implemented. The rule exists (so the pipeline shape and provenance
    are real and testable), but running it raises rather than corrupting the
    "corrected" claim with a no-op.
    """

    def __init__(self, name: str, version: str, description: str) -> None:
        self.name = name
        self.version = version
        self.description = description

    def apply(self, df: "pd.DataFrame") -> "pd.DataFrame":
        raise UnimplementedCorrection(
            f"TODO: implement correction rule {self.name!r} (v{self.version}): "
            f"{self.description}. Refusing to pass data through unchanged — a "
            "silent no-op would fabricate a 'corrected' dataset."
        )
