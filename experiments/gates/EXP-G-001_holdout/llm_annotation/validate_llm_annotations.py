#!/usr/bin/env python3
"""Check and merge one LLM annotator's chunk replies.

Usage: python validate_llm_annotations.py responses/<model_name>

Checks every item in the manifest is answered exactly once, that directions come
from the allowed set, and that every feature name is in the vocabulary — a model
that invents feature names has not followed the task and its pass is not usable.
Writes ``merged.jsonl`` beside the chunk files on success.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIRS = {"+", "-", "unclear"}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    resp = (HERE / sys.argv[1]).resolve()
    manifest = json.loads((HERE / "chunks_manifest.json").read_text(encoding="utf-8"))
    vocab = set(json.loads((HERE.parent / "feature_vocabulary.json").read_text(encoding="utf-8")))
    batch = [json.loads(x) for x in
             (HERE.parent / "audit_batch.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    expected = [it["item_id"] for it in batch]

    seen, problems, rows = {}, [], []
    for chunk in manifest["chunks"]:
        path = resp / chunk["chunk"].replace(".md", ".jsonl")
        if not path.is_file():
            problems.append(f"missing reply file: {path.name}")
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"{path.name}:{n} is not JSON ({exc.msg}) — usually a truncated "
                                f"last line; ask the model to continue from that item")
                continue
            iid = rec.get("item_id")
            if iid in seen:
                problems.append(f"{path.name}:{n} duplicate answer for {iid}")
            seen[iid] = True
            for c in rec.get("claims") or []:
                if c.get("dir") not in DIRS:
                    problems.append(f"{iid}/{c.get('feature')}: bad dir {c.get('dir')!r}")
                if c.get("feature") not in vocab:
                    problems.append(f"{iid}: {c.get('feature')!r} is not a vocabulary feature")
                rows.append({"item_id": iid, "feature": c.get("feature"),
                             "dir": c.get("dir"), "hedged": bool(c.get("hedged"))})

    for iid in expected:
        if iid not in seen:
            problems.append(f"no answer for {iid}")

    print(f"items answered: {len(seen)}/{len(expected)}   claims: {len(rows)}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems[:40]:
            print("  -", p)
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1

    out = resp / "merged.jsonl"
    by_item = {}
    for r in rows:
        by_item.setdefault(r["item_id"], []).append(
            {"feature": r["feature"], "dir": r["dir"], "hedged": r["hedged"]})
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for iid in expected:
            fh.write(json.dumps({"item_id": iid, "claims": by_item.get(iid, [])},
                                ensure_ascii=False) + "\n")
    print(f"OK -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
