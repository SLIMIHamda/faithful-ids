"""Regenerate every figure from analysis outputs (`make figures`)."""

from __future__ import annotations

from paper.figures.src import fig_cd_diagram, fig_coverage_risk


def main() -> int:
    fig_cd_diagram.generate()
    fig_coverage_risk.generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
