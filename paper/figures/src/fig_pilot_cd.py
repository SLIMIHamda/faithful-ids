"""Figure: pilot critical-difference diagram (B0-B4 on real CICIDS2017).

Reads ``analysis/outputs/pilot_faithfulness/results.json`` ONLY. Emits a
deterministic ``.data.json`` and a rasterised ``.png``. Skips if the pilot
analysis output is absent (i.e. the real pilot has not been run in this checkout).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
INPUT = REPO / "analysis" / "outputs" / "pilot_faithfulness" / "results.json"
GEN = REPO / "paper" / "figures" / "generated"
PNG = GEN / "fig_pilot_cd.png"
DATA = GEN / "fig_pilot_cd.data.json"


def generate() -> None:
    if not INPUT.is_file():
        print("fig_pilot_cd: skip — run the pilot + analysis first")
        return
    res = json.loads(INPUT.read_text(encoding="utf-8"))["result"]
    methods, ranks, cd = res["methods"], res["avg_ranks"], res["critical_difference"]
    GEN.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps({
        "kind": "critical_difference", "metric": res.get("metric"), "methods": methods,
        "avg_ranks": [round(r, 6) for r in ranks], "critical_difference": round(cd, 6),
        "pvalue": round(res.get("pvalue", float("nan")), 6),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(6.5, 1.9))
    ax.set_xlim(0.5, len(methods) + 0.5); ax.set_ylim(0, 1)
    ax.hlines(0.5, 1, len(methods), color="black")
    for i in sorted(range(len(methods)), key=lambda i: ranks[i]):
        ax.plot([ranks[i]], [0.5], "o", color="tab:blue")
        ax.annotate(methods[i], (ranks[i], 0.56), ha="center", fontsize=8, rotation=15)
    ax.plot([1, 1 + cd], [0.2, 0.2], color="tab:red")
    ax.annotate(f"CD={cd:.2f}", (1 + cd / 2, 0.08), ha="center", fontsize=8, color="tab:red")
    ax.set_yticks([]); ax.set_xlabel(f"avg rank ({res.get('metric')}, lower=better)")
    ax.set_title("Pilot CD diagram — B0-B4 faithfulness (CICIDS2017, NON-CITABLE)")
    fig.tight_layout(); fig.savefig(PNG, dpi=110); plt.close(fig)
    print(f"fig_pilot_cd: wrote {DATA.name} (+ {PNG.name})")


if __name__ == "__main__":
    generate()
