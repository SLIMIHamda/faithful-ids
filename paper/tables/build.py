"""Regenerate every table from analysis outputs (`make tables`)."""

from __future__ import annotations

from paper.tables.src import tab_layer1_summary


def main() -> int:
    tab_layer1_summary.generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
