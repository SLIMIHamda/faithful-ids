"""Figure: capability-anchored scaling — faithfulness vs measured capability.

Reads ``analysis/outputs/capability_scaling/results.json`` ONLY. Skips if absent
or if the capability anchor is not yet populated (MMLU null → ``capability_populated``
False), so it never fabricates an x-axis. NON-CITABLE.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
INPUT = REPO / "analysis" / "outputs" / "capability_scaling" / "results.json"
GEN = REPO / "paper" / "figures" / "generated"
PNG = GEN / "fig_capability_scaling.png"
DATA = GEN / "fig_capability_scaling.data.json"


def generate() -> None:
    if not INPUT.is_file():
        print("fig_capability_scaling: skip — capability_scaling analysis not run")
        return
    res = json.loads(INPUT.read_text(encoding="utf-8"))["result"]
    if not res.get("capability_populated"):
        print("fig_capability_scaling: skip — capability anchor not populated "
              "(MMLU null; fill analysis/data/capability_anchor.yaml)")
        return
    points, metric, gens = res["points"], res["metric"], res["generators"]
    xs = [p["mmlu"] for p in points]
    GEN.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps({
        "kind": "capability_scaling", "metric": metric, "x": "mmlu",
        "points": points,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    for g in gens:
        ys = [p["faithfulness"].get(g) for p in points]
        pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        if pairs:
            gx, gy = zip(*sorted(pairs))
            ax.plot(gx, gy, marker="o", label=g)
    ax.set_xlabel("MMLU (capability)"); ax.set_ylabel(f"Layer-1 {metric}")
    ax.set_title("Faithfulness vs capability (NON-CITABLE)")
    ax.set_ylim(0, 1.02); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(PNG, dpi=110); plt.close(fig)
    print(f"fig_capability_scaling: wrote {DATA.name} (+ {PNG.name})")


if __name__ == "__main__":
    generate()
