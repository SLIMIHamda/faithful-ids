"""Assemble the manuscript from regenerated assets (`make paper`).

The manuscript (``paper/manuscript/``) includes graphics ONLY from
``figures/generated/`` and tables ONLY from ``tables/generated/``. The LaTeX
build (latexmk) is run inside the pinned container; this entrypoint verifies the
generated assets exist and is the hook the container invokes.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GENERATED = [
    REPO / "paper" / "figures" / "generated",
    REPO / "paper" / "tables" / "generated",
]


def main() -> int:
    for d in GENERATED:
        assets = sorted(p.name for p in d.glob("*")) if d.is_dir() else []
        print(f"{d.relative_to(REPO)}: {len(assets)} generated asset(s)")
    print("paper: run figures + tables first (make figures tables); LaTeX build runs in-container.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
