"""The correction pipeline: ordered rules + checksum verification (L1).

Applies an ordered list of :class:`CorrectionRule` to a raw dataframe, verifying
the input checksum before and recording the output checksum after, and emits the
``CORRECTIONS_APPLIED.md`` record of the exact fix-set. The pipeline never
mutates ``raw/`` (raw data is sacred); it returns a corrected copy that the
caller writes under ``corrected/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from faithfulids.datasets.corrections.base import CorrectionRule
from faithfulids.provenance.hashing import sha256_text

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd


class ChecksumMismatch(RuntimeError):
    """Raised when the input dataframe does not match its expected checksum."""


def dataframe_sha256(df: "pd.DataFrame") -> str:
    """Deterministic content hash of a dataframe (column-order sensitive)."""
    # canonical CSV bytes; index dropped so re-materialisation is stable
    return sha256_text(df.to_csv(index=False))


@dataclass
class CorrectionPipeline:
    version: str
    rules: Sequence[CorrectionRule]

    def describe(self) -> list[dict[str, str]]:
        """The fix-set, for CORRECTIONS_APPLIED.md and manifests."""
        return [{"name": r.name, "version": r.version} for r in self.rules]

    def apply(
        self, df: "pd.DataFrame", *, expected_input_sha256: str | None = None
    ) -> "pd.DataFrame":
        """Apply every rule in order, returning the corrected dataframe.

        Verifies the input checksum first (if provided). Any unimplemented rule
        raises (never a silent pass-through).
        """
        if expected_input_sha256 is not None:
            actual = dataframe_sha256(df)
            if actual != expected_input_sha256:
                raise ChecksumMismatch(
                    f"raw input checksum mismatch: expected {expected_input_sha256[:12]}…, "
                    f"got {actual[:12]}…"
                )
        out = df
        for rule in self.rules:
            out = rule.apply(out)
        return out

    def write_corrections_applied(
        self, path: str | Path, *, input_sha256: str, output_sha256: str
    ) -> Path:
        """Write the human+machine record of the exact fix-set applied."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Corrections applied",
            "",
            f"Pipeline version: `{self.version}`",
            "",
            f"- input sha256: `{input_sha256}`",
            f"- output sha256: `{output_sha256}`",
            "",
            "## Fix-set (in order)",
            "",
        ]
        for r in self.rules:
            lines.append(f"- `{r.name}` v{r.version}")
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p
