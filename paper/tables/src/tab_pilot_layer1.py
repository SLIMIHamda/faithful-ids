"""Table: pilot Layer-1 faithfulness per generator (real CICIDS2017).

Reads ``analysis/outputs/pilot_faithfulness/results.json`` ONLY. Skips if absent.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INPUT = REPO / "analysis" / "outputs" / "pilot_faithfulness" / "results.json"
GEN = REPO / "paper" / "tables" / "generated"
TEX = GEN / "tab_pilot_layer1.tex"
DATA = GEN / "tab_pilot_layer1.data.json"


def generate() -> None:
    if not INPUT.is_file():
        print("tab_pilot_layer1: skip — run the pilot + analysis first")
        return
    res = json.loads(INPUT.read_text(encoding="utf-8"))["result"]
    methods, scores, ranks = res["methods"], res["scores"], res["avg_ranks"]
    means = [round(sum(r) / len(r), 6) if r else 0.0 for r in scores]
    GEN.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps({
        "methods": methods, "mean_mention_f1": means, "avg_rank": [round(r, 6) for r in ranks],
        "metric": res.get("metric"), "pvalue": round(res.get("pvalue", float("nan")), 6),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "% GENERATED — pilot, NON-CITABLE. Source: analysis/outputs/pilot_faithfulness.",
        "\\begin{tabular}{lrr}", "\\toprule",
        "Generator & Mean mention F1 & Avg rank \\\\", "\\midrule",
    ]
    for m, mean, rank in zip(methods, means, ranks):
        lines.append(f"{m.replace('_', chr(92)+'_')} & {mean:.3f} & {rank:.2f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    TEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"tab_pilot_layer1: wrote {TEX.name} (+ {DATA.name})")


if __name__ == "__main__":
    generate()
