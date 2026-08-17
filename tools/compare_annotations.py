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
import hashlib
import json
import re
from itertools import combinations
from pathlib import Path

#: A claim counts as directional only for these; 'unclear'/'absent' are not claims.
DIRECTIONAL = ("+", "-")
ABSENT = "absent"


def load_human(path: Path) -> dict[tuple[str, str], str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(r["item_id"], r["feature"]): r["text_asserts_direction"]
            for r in data["annotations"] if "feature" in r}


#: Replies arrive named by whoever saved them — .jsonl, .json and .txt all show
#: up in practice, and the content is JSONL regardless of the extension.
RESPONSE_SUFFIXES = (".jsonl", ".json", ".txt")


def load_llm(path: Path) -> dict[tuple[str, str], str]:
    """A JSONL pass: one {'item_id', 'claims':[{feature, dir}]} per line.

    utf-8-sig, because a reply pasted through a text editor on Windows often
    carries a BOM that would otherwise break the first line.
    """
    out: dict[tuple[str, str], str] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path.name}:{n} is not JSON ({exc.msg}) — usually a truncated "
                             f"reply; ask the model to continue from that item")
        for c in rec.get("claims") or []:
            out[(rec["item_id"], c["feature"])] = c.get("dir")
    return out


def covered(path: Path, is_human: bool) -> set[str]:
    """The items a pass actually answered — NOT the items it made claims about.

    A free-recall pass legitimately returns ``claims: []`` for an item that
    discusses no feature, and that is an answer. Coverage therefore comes from
    the item ids present in the file, so a partial annotator's unanswered items
    can be excluded rather than silently read as a wall of ``absent``.
    """
    if is_human:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {r["item_id"] for r in data["annotations"] if "feature" in r}
    out = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            out.add(json.loads(line)["item_id"])
    return out


def discover(probe: Path, include: str | None,
             humans: list[Path] | None = None) -> tuple[dict[str, dict], dict[str, set]]:
    """Every pass under ``probe``, de-duplicated by content.

    Accepts both layouts: flat files in ``responses/`` (one file per pass) and a
    directory per model holding chunk replies, which are merged into one pass.
    The same reply often gets saved twice under different extensions or
    concatenated into an ``all`` file; counting it twice would inflate agreement
    and bias the alpha, so identical content is dropped and a chunk file whose
    items are already covered by a sibling aggregate is not double counted.
    """
    passes: dict[str, dict] = {}
    cover: dict[str, set] = {}
    seen: dict[str, str] = {}

    def add(name: str, files: list[Path], is_human: bool) -> None:
        labels: dict[tuple[str, str], str] = {}
        items: set[str] = set()
        for f in files:
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            if digest in seen:
                print(f"note: {f.name} is byte-identical to {seen[digest]} — counted once")
                continue
            seen[digest] = f.name
            new = covered(f, is_human)
            if new & items:
                print(f"note: {f.name} repeats items already loaded for {name} — skipped "
                      f"(looks like an aggregate of the chunk files)")
                continue
            items |= new
            labels.update(load_human(f) if is_human else load_llm(f))
        if labels:
            passes[name] = labels
            cover[name] = items

    for f in sorted(probe.glob("human_*.json")):
        add(f.stem.replace("human_", ""), [f], True)

    for h in humans or []:
        add(h.stem.replace("human_", "").replace("annotations_", ""), [h], True)

    for resp in (probe / "responses", probe / "llm_annotation" / "responses"):
        if not resp.is_dir():
            continue
        for d in sorted(p for p in resp.iterdir() if p.is_dir()):
            files = sorted(f for f in d.rglob("*")
                           if f.suffix.lower() in RESPONSE_SUFFIXES
                           and re.search(r"chunk[_-]?\d+", f.name, re.I))
            extra = sorted(f for f in d.rglob("*")
                           if f.suffix.lower() in RESPONSE_SUFFIXES and f not in files)
            if include and include.lower() not in d.name.lower():
                continue
            add(d.name, files + extra, False)
        for f in sorted(p for p in resp.iterdir()
                        if p.is_file() and p.suffix.lower() in RESPONSE_SUFFIXES):
            if include and include.lower() not in f.name.lower():
                continue
            add(f.stem, [f], False)
    return passes, cover


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
    ap.add_argument("--human", type=Path, action="append",
                    help="extra human export to include (repeatable)")
    ap.add_argument("--include", help="substring filter on response filenames, e.g. 'matched'. "
                                      "Matched and free-recall are DIFFERENT tasks — pooling "
                                      "them in one comparison mixes two elicitations.")
    args = ap.parse_args(argv)

    passes, cover = discover(args.probe, args.include, args.human)
    if len(passes) < 2:
        print(f"need at least two passes; found {list(passes)} in {args.probe}")
        return 2

    src = args.probe / "probe_items.json"
    if src.is_file():
        items = json.loads(src.read_text(encoding="utf-8"))
    else:  # full batch: candidates live in audit_batch.jsonl
        items = {it["item_id"]: it
                 for line in (args.probe / "audit_batch.jsonl").read_text(
                     encoding="utf-8").splitlines() if line.strip()
                 for it in [json.loads(line)]}

    # Restrict to items EVERY pass answered. Imputing 'absent' for an item an
    # annotator never saw would score their silence as a judgment — the 17-item
    # human pass beside a 300-item LLM pass would otherwise read as 283 items of
    # perfect disagreement.
    shared = set(items)
    for c in cover.values():
        shared &= c
    dropped = len(items) - len(shared)
    items = {k: v for k, v in items.items() if k in shared}

    units = {(iid, f) for iid, it in items.items() for f in it["candidates"]}
    for name, p in passes.items():
        units |= {u for u in p if u[0] in shared}
    units = sorted(units)

    print("passes:")
    for name in passes:
        print(f"  {name:<34} answered {len(cover[name]):>3} items")
    if dropped:
        print(f"\nrestricted to the {len(shared)} items every pass answered "
              f"({dropped} dropped — not all passes covered them)")
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

    key_path = args.key or next(
        (c for c in (args.probe / "audit_key_DO_NOT_SHOW_ANNOTATOR.json",
                     args.probe.parent / "audit_key_DO_NOT_SHOW_ANNOTATOR.json")
         if c.is_file()), args.probe / "missing.json")
    if key_path.is_file():
        key = json.loads(key_path.read_text(encoding="utf-8"))
        print("\n=== each pass vs the EXTRACTOR (directional claims only) ===")
        print(f"{'pass':<28}{'precision':>11}{'recall':>9}{'F1':>9}   (extractor as prediction)")
        extractor = {(iid, c["feature"]): c["direction"]
                     for iid in items for c in key[iid]["extractor_claims"]}
        pred = {(u, d) for u, d in extractor.items() if d in DIRECTIONAL}
        for name, p in passes.items():
            # gold must live on the SAME item set as the prediction, or a pass
            # covering more items than the comparison scores its extra claims as
            # misses and recall collapses
            gold = {(u, d) for u, d in p.items() if d in DIRECTIONAL and u[0] in shared}
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

    out = args.probe / (f"comparison_{args.include}.json" if args.include else "comparison.json")
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
