#!/usr/bin/env python3
"""Score EXP-G-001: the extractor against adjudicated gold, and write the verdict.

Implements prereg amendment 0004. The rule it enforces, on **both** sides of the
comparison:

    A claim is directional only when the text gives explicit directional
    evidence. Inference by default is never directional evidence.

so gold excludes what the annotators marked ``unclear``/``absent``, and the
prediction set excludes any extractor claim whose ``direction_evidence`` is
``"default"`` — a sign the rule engine supplied because it found no cue is not a
parsed claim. Scoring it as one is what let the lenient reading return F1 0.975
while a third of the claims were guesses.

Reports, per amendment 0004(C), together and never separately:

1. overall precision / recall / F1 against adjudicated gold;
2. the same split by ``direction_evidence`` (``word`` / ``number`` / ``default``);
3. the count and proportion of extractor claims resting on ``default``.

Adjudication. Cells the two annotators agree on need none. Disagreements need a
human, and the gate spec requires it — but the verdict does not always depend on
them, so this reports the F1 under **both extremes** (every disagreement resolved
toward one annotator, then the other). When both extremes fall the same side of
the threshold, adjudication cannot change the verdict and the tool says so; when
they straddle it, the tool refuses to declare a verdict until an adjudication
file exists.

Run::

    python tools/score_audit_gate.py --batch experiments/gates/EXP-G-001_audit_v2 \\
        --pass LLM_1_V2 --pass LLM_2_V2 [--adjudication FILE] [--write-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from compare_annotations import (  # noqa: E402
    cohens_kappa,
    krippendorff_nominal,
    load_llm,
)
from faithfulids.orchestration.references import resolve_reference  # noqa: E402

DIRECTIONAL = ("+", "-")
ABSENT = "absent"
#: A claim the rule engine could not parse. Amendment 0004: never gold, never
#: prediction — on either side of the comparison.
DEFAULT_EVIDENCE = "default"


def load_pass(batch: Path, name: str) -> dict[tuple[str, str], str]:
    d = batch / "llm_annotation" / "responses" / name
    if not d.is_dir():
        raise SystemExit(f"no such pass: {d}")
    labels: dict[tuple[str, str], str] = {}
    files = sorted(f for f in d.glob("*.jsonl") if "chunk" in f.name.lower())
    if not files:
        raise SystemExit(f"{d}: no chunk_NN.jsonl replies")
    for f in files:
        labels.update(load_llm(f))
    return labels


def prf(pred: set, gold: set) -> tuple[float, float, float, int]:
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0), tp


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--pass", dest="passes", action="append", required=True,
                    help="response directory name (give exactly two)")
    ap.add_argument("--adjudication", type=Path,
                    help='JSON {"item_id|feature": "+"|"-"|"unclear"|"absent"}')
    ap.add_argument("--claims-key", default="extractor_claims_1_5_0",
                    help="key in the audit key holding the extractor claims to score")
    ap.add_argument("--write-run", action="store_true",
                    help="write a runs/EXP-G-001/ run stamping manifest.gate")
    args = ap.parse_args(argv)

    if len(args.passes) != 2:
        raise SystemExit("the gate registers TWO annotators; give exactly two --pass")

    batch = args.batch
    items = {it["item_id"]: it for line in (batch / "audit_batch.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip() for it in [json.loads(line)]}
    key = json.loads((batch / "audit_key_DO_NOT_SHOW_ANNOTATOR.json").read_text(encoding="utf-8"))
    threshold = float(resolve_reference("statistics:decision_thresholds:extractor_f1")["value"])

    a_name, b_name = args.passes
    A, B = load_pass(batch, a_name), load_pass(batch, b_name)

    units = sorted({(i, f) for i, it in items.items() for f in it["candidates"]}
                   | set(A) | set(B))
    agree, kappa = cohens_kappa(A, B, units)
    alpha = krippendorff_nominal([A, B], units)
    disputed = [u for u in units if A.get(u, ABSENT) != B.get(u, ABSENT)]

    print(f"batch:      {batch.name}   {len(items)} items, {len(units)} cells")
    print(f"annotators: {a_name}, {b_name}")
    print(f"agreement:  {agree:.4f}   Cohen kappa {kappa:.4f}   "
          f"Krippendorff alpha {'n/a' if alpha is None else f'{alpha:.4f}'}")
    print(f"disputed:   {len(disputed)} cells\n")

    adjud: dict[tuple[str, str], str] = {}
    if args.adjudication:
        for k, v in json.loads(args.adjudication.read_text(encoding="utf-8")).items():
            iid, feat = k.split("|", 1)
            adjud[(iid, feat)] = v
        missing = [u for u in disputed if u not in adjud]
        if missing:
            print(f"WARNING: adjudication file misses {len(missing)} disputed cells\n")

    # --- the extractor's claims, split by how it got the direction ----------- #
    claims = [(iid, c) for iid in items for c in key[iid][args.claims_key]]
    n_dir = sum(1 for _, c in claims if c["direction"] in DIRECTIONAL)
    n_def = sum(1 for _, c in claims
                if c["direction"] in DIRECTIONAL and c["direction_evidence"] == DEFAULT_EVIDENCE)
    print(f"extractor ({args.claims_key}): {n_dir} directional claims, "
          f"{n_def} from DEFAULT ({n_def / n_dir:.1%}) — amendment 0004(C)")

    pred_parsed = {((iid, c["feature"]), c["direction"]) for iid, c in claims
                   if c["direction"] in DIRECTIONAL
                   and c["direction_evidence"] != DEFAULT_EVIDENCE}
    pred_all = {((iid, c["feature"]), c["direction"]) for iid, c in claims
                if c["direction"] in DIRECTIONAL}

    def gold_for(fallback: dict) -> set:
        out = set()
        for u in units:
            va, vb = A.get(u, ABSENT), B.get(u, ABSENT)
            v = va if va == vb else adjud.get(u, fallback.get(u, ABSENT))
            if v in DIRECTIONAL:
                out.add((u, v))
        return out

    print(f"\n=== VERDICT (amendment 0004: defaults excluded both sides) ===")
    print(f"{'gold resolution':<34}{'precision':>11}{'recall':>9}{'F1':>9}{'':>4}")
    results = {}
    for label, fb in ((f"agreed + adjudicated", {}),
                      (f"disputed -> {a_name}", A),
                      (f"disputed -> {b_name}", B)):
        gold = gold_for(fb)
        p, r, f1, tp = prf(pred_parsed, gold)
        results[label] = {"precision": p, "recall": r, "f1": f1, "tp": tp,
                          "n_gold": len(gold), "n_pred": len(pred_parsed)}
        mark = "PASS" if f1 >= threshold else "FAIL"
        print(f"{label:<34}{p:>11.3f}{r:>9.3f}{f1:>9.3f}   {mark}")

    lo = min(results[k]["f1"] for k in results if k.startswith("disputed"))
    hi = max(results[k]["f1"] for k in results if k.startswith("disputed"))
    decided = (lo >= threshold) == (hi >= threshold)
    print(f"\nsensitivity to adjudication: F1 in [{lo:.3f}, {hi:.3f}], threshold {threshold}")
    print("  -> adjudication CANNOT change the verdict" if decided else
          "  -> the extremes STRADDLE the threshold: adjudication decides. "
          "Supply --adjudication before claiming a verdict.")

    print(f"\n=== split by direction_evidence (amendment 0004(C)) ===")
    gold = gold_for({})
    print(f"{'evidence':<12}{'claims':>8}{'precision':>11}{'recall*':>9}{'F1*':>9}"
          "   (*recall vs the whole gold set)")
    for ev in ("word", "number", DEFAULT_EVIDENCE):
        sub = {((iid, c["feature"]), c["direction"]) for iid, c in claims
               if c["direction"] in DIRECTIONAL and c["direction_evidence"] == ev}
        p, r, f1, _ = prf(sub, gold)
        print(f"{ev:<12}{len(sub):>8}{p:>11.3f}{r:>9.3f}{f1:>9.3f}")
    p_all, r_all, f_all, _ = prf(pred_all, gold)
    print(f"\nfor contrast, scoring defaults AS IF parsed: "
          f"P {p_all:.3f}  R {r_all:.3f}  F1 {f_all:.3f}"
          f"  <-- what amendment 0004 forbids")

    verdict = results["agreed + adjudicated"]["f1"] >= threshold and decided
    payload = {
        "batch": batch.name, "annotators": [a_name, b_name],
        "n_items": len(items), "n_cells": len(units),
        "agreement": agree, "cohens_kappa": kappa, "krippendorff_alpha": alpha,
        "n_disputed": len(disputed),
        "disputed_cells": [{"item_id": i, "feature": f, a_name: A.get((i, f), ABSENT),
                            b_name: B.get((i, f), ABSENT)} for i, f in disputed],
        "extractor_claims_key": args.claims_key,
        "n_directional_claims": n_dir, "n_default": n_def, "default_share": n_def / n_dir,
        "threshold": threshold, "results": results,
        "adjudication_can_change_verdict": not decided,
        "passed": bool(verdict),
    }
    out = batch / "gate_result.json"
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")
    print(f"\nGATE {'PASSED' if verdict else 'FAILED'} "
          f"(F1 {results['agreed + adjudicated']['f1']:.3f} vs threshold {threshold})")

    if args.write_run:
        print("\n--write-run: not yet wired — the run writer needs the artifact shape "
              "agreed first; gate_result.json holds the verdict meanwhile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
