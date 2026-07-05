"""Figure: critical-difference diagram (H1 headline pattern).

Reads ``analysis/outputs/toy_demo/results.json`` ONLY (no faithfulids import).
Emits a deterministic numeric sidecar (``.data.json`` — the diffed artifact) and
a rasterised ``.png`` (a regenerable build product; see the tolerance policy).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
INPUT = REPO / "analysis" / "outputs" / "toy_demo" / "results.json"
GEN = REPO / "paper" / "figures" / "generated"
PNG = GEN / "fig_cd_diagram.png"
DATA = GEN / "fig_cd_diagram.data.json"


def generate() -> None:
    if not INPUT.is_file():
        print("fig_cd_diagram: skip — analysis/outputs/toy_demo not present")
        return
    res = json.loads(INPUT.read_text(encoding="utf-8"))["result"]
    methods, ranks, cd = res["methods"], res["avg_ranks"], res["critical_difference"]

    GEN.mkdir(parents=True, exist_ok=True)
    data = {
        "kind": "critical_difference",
        "metric": res.get("metric"),
        "methods": methods,
        "avg_ranks": [round(r, 6) for r in ranks],
        "critical_difference": round(cd, 6),
    }
    DATA.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    order = sorted(range(len(methods)), key=lambda i: ranks[i])
    fig, ax = plt.subplots(figsize=(6.0, 1.8))
    ax.set_xlim(0.5, len(methods) + 0.5)
    ax.set_ylim(0, 1)
    ax.hlines(0.5, 1, len(methods), color="black")
    for i in order:
        ax.plot([ranks[i]], [0.5], "o", color="tab:blue")
        ax.annotate(methods[i], (ranks[i], 0.55), ha="center", fontsize=8)
    ax.plot([1, 1 + cd], [0.2, 0.2], color="tab:red")
    ax.annotate(f"CD={cd:.2f}", (1 + cd / 2, 0.1), ha="center", fontsize=8, color="tab:red")
    ax.set_yticks([])
    ax.set_xlabel(f"average rank ({res.get('metric')}, lower = better)")
    ax.set_title("Critical-difference diagram (toy fixture, NON-CITABLE)")
    fig.tight_layout()
    fig.savefig(PNG, dpi=100)
    plt.close(fig)
    print(f"fig_cd_diagram: wrote {DATA.name} (+ {PNG.name})")


if __name__ == "__main__":
    generate()
