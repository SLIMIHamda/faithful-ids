"""Table: Layer-1 mean faithfulness per generator (LaTeX, emitted not typed).

Reads ``analysis/outputs/toy_demo/results.json`` ONLY. Emits a deterministic
``.tex`` (the diffed artifact) and a ``.data.json`` sidecar.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INPUT = REPO / "analysis" / "outputs" / "toy_demo" / "results.json"
GEN = REPO / "paper" / "tables" / "generated"
TEX = GEN / "tab_layer1_summary.tex"
DATA = GEN / "tab_layer1_summary.data.json"


def generate() -> None:
    if not INPUT.is_file():
        print("tab_layer1_summary: skip — analysis/outputs/toy_demo not present")
        return
    res = json.loads(INPUT.read_text(encoding="utf-8"))["result"]
    methods, scores = res["methods"], res["scores"]
    means = [round(sum(row) / len(row), 6) if row else 0.0 for row in scores]

    GEN.mkdir(parents=True, exist_ok=True)
    DATA.write_text(
        json.dumps({"methods": methods, "mean": means, "metric": res.get("metric")},
                   indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "% GENERATED — do not edit. Source: analysis/outputs/toy_demo (NON-CITABLE).",
        "\\begin{tabular}{lr}",
        "\\toprule",
        f"Generator & Mean {res.get('metric')} \\\\",
        "\\midrule",
    ]
    for m, mean in zip(methods, means):
        safe = m.replace("_", "\\_")
        lines.append(f"{safe} & {mean:.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    TEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"tab_layer1_summary: wrote {TEX.name} (+ {DATA.name})")


if __name__ == "__main__":
    generate()
