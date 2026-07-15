"""Regenerate every figure from analysis outputs (`make figures`)."""

from __future__ import annotations

from paper.figures.src import (
    fig_capability_scaling,
    fig_cd_diagram,
    fig_coverage_risk,
    fig_pilot_cd,
    fig_pilot_coverage,
)


def main() -> int:
    fig_cd_diagram.generate()
    fig_coverage_risk.generate()
    fig_pilot_cd.generate()          # skips unless the real pilot has been run
    fig_pilot_coverage.generate()    # skips unless the real pilot has been run
    fig_capability_scaling.generate()  # skips unless runs + capability anchor populated
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
