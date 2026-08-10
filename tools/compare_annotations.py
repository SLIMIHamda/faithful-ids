#!/usr/bin/env python3
"""Compare annotation passes with each other and with the extractor.

Reads every pass in a probe directory — the human export from ``annotator.html``
and any LLM replies under ``responses/`` — puts them on a common unit set, and
reports:

* **pairwise agreement and Cohen's kappa** — raw agreement alone is inflated
  here because ``absent`` is common, and two annotators who both say ``absent``
  a lot will look like they agree when they are only both being conservative;
* **Krippendorff alpha** over all passes at once, the statistic the gate asks for;
* **the actual disagreeing cells**, because a number does not tell you whether a
  model is systematically wrong in one direction or noisy everywhere;
* **each pass scored against the extractor** — precision, recall and F1 over
  directional claims, which is what EXP-G-001 measures.

The unit set is every (item, feature) pair any pass mentions. A pass that does
not mention a pair is treated as saying ``absent`` for it: a feature one
annotator claims and another omits is a **disagreement**, not missing data.
Free-recall passes never say ``absent`` explicitly, which is exactly why the
omission has to be given a value rather than dropped.

Run::

    python tools/compare_annotations.py --probe <probe_dir>
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

#: A claim counts as directional only for these; 'unclear'/'absent' are not claims.
DIRECTIONAL = ("+", "-")
ABSENT = "absent"


def load_human(path: Path) -> dict[tuple[str, str], str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(r["item_id"], r["feature"]): r["text_asserts_direction"]
            for r in data["annotations"] if "feature" in r}


def load_llm(path: Path) -> dict[tuple[str, str], str]:
    """A JSONL pass: one {'item_id', 'claims':[{feature, dir}]} per line."""
    out: dict[tuple[str, str], str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        for c in rec.get("claims") or []:
            out[(rec["item_id"], c["feature"])] = c.get("dir")
    return out


def krippendorff_nominal(passes: list[dict[tuple[str, str], str]], units: list) -> float | None:
    """Nominal alpha via the coincidence matrix. None when it is undefined."""
    coincidence: dict[tuple[str, str], float] = {}
    totals: dict[str, float] = {}
    for u in units:
        vals = [p.get(u, ABSENT) for p in passes]
        m = len(vals)
        if m < 2:
            continue
        for a in vals:
            for b in vals:
                if a is b and vals.count(a) == 1:
                    continue
        for idx_a, a in enumerate(vals):
            for idx_b, b in enumerate(vals):
                if idx_a == idx_b:
                    continue
                coincidence[(a, b)] = coincidence.get((a, b), 0.0) + 1.0 / (m - 1)
    for (a, _b), v in coincidence.items():
        totals[a] = totals.get(a, 0.0) + v
    n = sum(totals.values())
    if n <= 1:
        return None
    d_o = sum(v for (a, b), v in coincidence.items() if a != b)
    d_e = sum(totals[a] * totals[b] / (n - 1)
              for a in totals for b in totals if a != b)
    if d_e == 0:
        return None
    return 1.0 - d_o / d_e


def cohens_kappa(a: dict, b: dict, units: list) -> tuple[float, float]:
    """(observed agreement, kappa) for two passes over a shared unit set."""
    va = [a.get(u, ABSENT) for u in units]
    vb = [b.get(u, ABSENT) for u in units]
    n = len(units)
    po = sum(x == y for x, y in zip(va, vb)) / n if n else 0.0
    labels = set(va) | set(vb)
    pe = sum((va.count(c) / n) * (vb.count(c) / n) for c in labels) if n else 0.0
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return po, kappa


def prf(pred: set, gold: set) -> tuple[float, float, float]:
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", type=Path, required=True)
    ap.add_argument("--key", type=Path,
                    help="audit_key_DO_NOT_SHOW_ANNOTATOR.json (default: ../ of the probe)")
    ap.add_argument("--max-show", type=int, default=25, help="disagreeing cells to print")
    args = ap.parse_args(argv)

    passes: dict[str, dict] = {}
    for f in sorted(args.probe.glob("human_*.json")):
        passes[f.stem.replace("human_", "")] = load_human(f)
    for f in sorted((args.probe / "responses").glob("*.jsonl")):
        passes[f.stem] = load_llm(f)
    if len(passes) < 2:
        print(f"need at least two passes; found {list(passes)} in {args.probe}")
        return 2

    items = json.loads((args.probe / "probe_items.json").read_text(encoding="utf-8"))
    # Unit set: every candidate that was put to an annotator, plus anything any
    # pass named that was not on the list (a free-recall pass can do that).
    units = {(iid, f) for iid, it in items.items() for f in it["candidates"]}
    for p in passes.values():
        units |= set(p)
    units = sorted(units)

    print(f"passes: {', '.join(passes)}")
    print(f"units:  {len(units)} (item, feature) cells over {len(items)} items\n")

    print("=== label distribution ===")
    labels = sorted({v for p in passes.values() for v in p.values()} | {ABSENT})
    print(f"{'pass':<28}" + "".join(f"{c:>10}" for c in labels))
    for name, p in passes.items():
        counts = {c: 0 for c in labels}
        for u in units:
            counts[p.get(u, ABSENT)] = counts.get(p.get(u, ABSENT), 0) + 1
        print(f"{name:<28}" + "".join(f"{counts[c]:>10}" for c in labels))

    print("\n=== pairwise agreement ===")
    print(f"{'pair':<48}{'agree':>9}{'kappa':>9}")
    for a, b in combinations(passes, 2):
        po, k = cohens_kappa(passes[a], passes[b], units)
        print(f"{a + '  vs  ' + b:<48}{po:>9.3f}{k:>9.3f}")

    alpha = krippendorff_nominal(list(passes.values()), units)
    print(f"\nKrippendorff alpha (nominal, all passes): "
          f"{'undefined' if alpha is None else f'{alpha:.3f}'}")

    key_path = args.key or (args.probe.parent / "audit_key_DO_NOT_SHOW_ANNOTATOR.json")
    if key_path.is_file():
        key = json.loads(key_path.read_text(encoding="utf-8"))
        print("\n=== each pass vs the EXTRACTOR (directional claims only) ===")
        print(f"{'pass':<28}{'precision':>11}{'recall':>9}{'F1':>9}   (extractor as prediction)")
        extractor = {(iid, c["feature"]): c["direction"]
                     for iid in items for c in key[iid]["extractor_claims"]}
        pred = {(u, d) for u, d in extractor.items() if d in DIRECTIONAL}
        for name, p in passes.items():
            gold = {(u, d) for u, d in p.items() if d in DIRECTIONAL}
            pr, rc, f1 = prf(pred, gold)
            print(f"{name:<28}{pr:>11.3f}{rc:>9.3f}{f1:>9.3f}")
        print("\nNOTE: this is NOT the EXP-G-001 verdict. The gate scores the extractor "
              f"against ADJUDICATED gold on 300 items; this is {len(items)} items against "
              "each pass separately, before any adjudication.")

    print(f"\n=== disagreeing cells (first {args.max_show}) ===")
    names = list(passes)
    dis = [u for u in units
           if len({passes[n].get(u, ABSENT) for n in names}) > 1]
    print(f"{len(dis)} of {len(units)} cells disagree\n")
    print(f"{'item':<11}{'feature':<32}" + "".join(f"{n[:14]:>16}" for n in names))
    for u in dis[:args.max_show]:
        print(f"{u[0]:<11}{u[1][:31]:<32}" +
              "".join(f"{passes[n].get(u, ABSENT):>16}" for n in names))
    if len(dis) > args.max_show:
        print(f"... and {len(dis) - args.max_show} more")

    out = args.probe / "comparison.json"
    out.write_text(json.dumps({
        "passes": list(passes),
        "n_units": len(units),
        "n_items": len(items),
        "krippendorff_alpha": alpha,
        "pairwise": {f"{a}|{b}": dict(zip(("agreement", "kappa"),
                                          cohens_kappa(passes[a], passes[b], units)))
                     for a, b in combinations(passes, 2)},
        "disagreements": [{"item_id": u[0], "feature": u[1],
                           **{n: passes[n].get(u, ABSENT) for n in names}} for u in dis],
    }, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
