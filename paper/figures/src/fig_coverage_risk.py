"""Figure: coverage-risk curve + AURC (B4 abstention pattern).

Reads ``analysis/outputs/toy_coverage/results.json`` ONLY. Emits a deterministic
``.data.json`` sidecar and a rasterised ``.png`` build product.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
INPUT = REPO / "analysis" / "outputs" / "toy_coverage" / "results.json"
GEN = REPO / "paper" / "figures" / "generated"
PNG = GEN / "fig_coverage_risk.png"
DATA = GEN / "fig_coverage_risk.data.json"


def generate() -> None:
    if not INPUT.is_file():
        print("fig_coverage_risk: skip — analysis/outputs/toy_coverage not present")
        return
    res = json.loads(INPUT.read_text(encoding="utf-8"))["result"]
    coverage, risk, aurc = res["coverage"], res["selective_risk"], res["aurc"]

    GEN.mkdir(parents=True, exist_ok=True)
    data = {
        "kind": "coverage_risk",
        "coverage": [round(c, 6) for c in coverage],
        "selective_risk": [round(r, 6) for r in risk],
        "aurc": round(aurc, 6),
    }
    DATA.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    ax.step(coverage, risk, where="post", color="tab:blue")
    ax.set_xlabel("coverage")
    ax.set_ylabel("selective risk")
    ax.set_title(f"Coverage-risk (AURC={aurc:.3f}, toy, NON-CITABLE)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, max(risk) * 1.1 + 1e-9)
    fig.tight_layout()
    fig.savefig(PNG, dpi=100)
    plt.close(fig)
    print(f"fig_coverage_risk: wrote {DATA.name} (+ {PNG.name})")


if __name__ == "__main__":
    generate()
