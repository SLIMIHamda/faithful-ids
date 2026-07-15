#!/usr/bin/env python
"""Score a completed blind annotation of extractor_audit_batch_v1.

Merges annotator judgments with audit_batch.jsonl (extracted_direction,
shap_sign) and the hidden key, then reports per-group:
  extractor_correct = extracted_direction == text_asserts_direction
  text_correct      = text_asserts_direction == shap_sign  (top-5 claims only)
and the branch-decision statistics from README_PROTOCOL.md.

Usage: python score_audit.py <annotations.json> [--annotator NAME]
Accepts the annotator.html export format ({"annotations":[...]}) or a merged
LLM-response jsonl (one {"item_id","claims":[{feature,dir,hedged}]} per line).
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_annotations(path):
    """-> {(item_id, feature): {"dir": str, "hedged": bool}}, notes {item_id: str}"""
    text = Path(path).read_text(encoding="utf-8")
    ann, notes = {}, {}
    if text.lstrip().startswith("{") and '"annotations"' in text[:200]:
        for row in json.loads(text)["annotations"]:
            if "note" in row and "feature" not in row:
                notes[row["item_id"]] = row["note"]
                continue
            ann[(row["item_id"], row["feature"])] = {
                "dir": row["text_asserts_direction"], "hedged": bool(row.get("hedged"))}
    else:  # merged LLM jsonl
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            for c in rec["claims"]:
                ann[(rec["item_id"], c["feature"])] = {
                    "dir": c["dir"], "hedged": bool(c.get("hedged"))}
    return ann, notes


def binom_ci(k, n, z=1.96):
    """Wilson interval."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fisher_exact(a, b, c, d):
    """Two-sided Fisher exact p for table [[a,b],[c,d]] (pure python)."""
    def lchoose(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    row1, row2, col1 = a + b, c + d, a + c
    n = row1 + row2
    def lp(x):
        return (lchoose(row1, x) + lchoose(row2, col1 - x) - lchoose(n, col1))
    p_obs = lp(a)
    lo, hi = max(0, col1 - row2), min(row1, col1)
    total = 0.0
    for x in range(lo, hi + 1):
        px = lp(x)
        if px <= p_obs + 1e-9:
            total += math.exp(px)
    return min(1.0, total)


def rate(k, n):
    if n == 0:
        return "  n/a      "
    lo, hi = binom_ci(k, n)
    return f"{k / n:6.3f} [{lo:.3f},{hi:.3f}] ({k}/{n})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("annotations")
    ap.add_argument("--annotator", default="human")
    args = ap.parse_args()

    batch = {}
    for line in (HERE / "audit_batch.jsonl").read_text(encoding="utf-8").splitlines():
        it = json.loads(line)
        batch[it["item_id"]] = it
    key = json.loads((HERE / "audit_key_DO_NOT_SHOW_ANNOTATOR.json").read_text(encoding="utf-8"))
    ann, notes = load_annotations(args.annotations)

    # ---- completeness ----
    missing = [(iid, c["feature"]) for iid, it in batch.items()
               for c in it["claims"] if (iid, c["feature"]) not in ann]
    print(f"annotator: {args.annotator}")
    print(f"judged claims: {len(ann)} / {sum(len(it['claims']) for it in batch.values())}"
          f"   (missing: {len(missing)})")
    for m in missing[:10]:
        print("   missing:", m)
    if len(missing) > 10:
        print(f"   ... and {len(missing) - 10} more")

    # ---- per-claim merge ----
    rows = []
    for iid, it in batch.items():
        g = key[iid]["group"]
        for c in it["claims"]:
            a = ann.get((iid, c["feature"]))
            if a is None:
                continue
            rows.append({
                "item_id": iid, "group": g, "feature": c["feature"],
                "generator": key[iid]["generator"],
                "extracted": c["extracted_direction"], "shap": c["shap_sign"],
                "text": a["dir"], "hedged": a["hedged"],
                "extractor_correct": c["extracted_direction"] == a["dir"],
                "text_correct": (a["dir"] == c["shap_sign"])
                                 if (c["shap_sign"] in ("+", "-") and a["dir"] in ("+", "-"))
                                 else None,
            })

    groups = sorted(set(r["group"] for r in rows))
    print("\n=== per-group rates (claim-level) ===")
    hdr = f"{'group':<12}{'n':>5}   {'extractor_correct':<28}{'text_correct (top-5, directional)':<30}{'hedged':<24}{'unclear':>8}{'absent':>8}"
    print(hdr)
    stats = {}
    for g in groups:
        rs = [r for r in rows if r["group"] == g]
        n = len(rs)
        ec = sum(r["extractor_correct"] for r in rs)
        tc_rows = [r for r in rs if r["text_correct"] is not None]
        tc = sum(r["text_correct"] for r in tc_rows)
        hg = sum(r["hedged"] for r in rs)
        un = sum(r["text"] == "unclear" for r in rs)
        ab = sum(r["text"] == "absent" for r in rs)
        stats[g] = dict(n=n, ec=ec, tc=tc, tcn=len(tc_rows), hg=hg)
        print(f"{g:<12}{n:>5}   {rate(ec, n):<28}{rate(tc, len(tc_rows)):<30}{rate(hg, n):<24}{un:>8}{ab:>8}")

    # ---- branch decision: degraded vs control ----
    if "degraded" in stats and "control" in stats:
        d, c = stats["degraded"], stats["control"]
        print("\n=== branch decision (degraded vs control) ===")
        p_ec = fisher_exact(d["n"] - d["ec"], d["ec"], c["n"] - c["ec"], c["ec"])
        print(f"extractor-ERROR rate: degraded {(d['n']-d['ec'])/d['n']:.3f} vs control "
              f"{(c['n']-c['ec'])/c['n']:.3f}   Fisher p = {p_ec:.2e}")
        p_tc = fisher_exact(d["tcn"] - d["tc"], d["tc"], c["tcn"] - c["tc"], c["tcn"])
        print(f"text-ERROR rate     : degraded {(d['tcn']-d['tc'])/max(d['tcn'],1):.3f} vs control "
              f"{(c['tcn']-c['tc'])/max(c['tcn'],1):.3f}   Fisher p = {p_tc:.2e}")
        print("reading: extractor-error >> control => Branch 2 (instrument);")
        print("         extractor-error comparable but text-error higher on degraded => Branch 1 or 3 (genuine).")

    # ---- disagreement dump for review ----
    out = HERE / f"scored_{args.annotator}.jsonl"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    dis = [r for r in rows if not r["extractor_correct"]]
    print(f"\nfull merge -> {out.name}   (extractor/text disagreements: {len(dis)})")
    if notes:
        print(f"annotator notes on {len(notes)} items:")
        for iid, t in notes.items():
            print(f"   {iid}: {t}")


if __name__ == "__main__":
    sys.exit(main())
