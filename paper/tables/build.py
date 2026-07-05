"""Regenerate every table from analysis outputs (`make tables`)."""

from __future__ import annotations

from paper.tables.src import tab_layer1_summary, tab_pilot_layer1


def main() -> int:
    tab_layer1_summary.generate()
    tab_pilot_layer1.generate()  # skips unless the real pilot has been run
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
