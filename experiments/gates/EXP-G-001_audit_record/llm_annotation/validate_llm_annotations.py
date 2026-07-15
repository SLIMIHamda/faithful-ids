#!/usr/bin/env python
"""Validate (and merge) LLM annotation responses for extractor_audit_batch_v1.

Usage:
    python validate_llm_annotations.py responses/<model_name>

Checks every chunk_NN.jsonl in the folder against chunks_manifest.json:
item ids present and in scope, every listed feature judged exactly once with a
valid dir, hedged a bool (forced false on unclear/absent). If everything passes,
writes merged file  responses/<model_name>_merged.jsonl  (one line per item).
Tolerates code fences, blank lines, and pretty-printed JSON arrays.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "chunks_manifest.json").read_text(encoding="utf-8"))
BATCH = {}
for line in (HERE.parent / "audit_batch.jsonl").read_text(encoding="utf-8").splitlines():
    it = json.loads(line)
    BATCH[it["item_id"]] = [c["feature"] for c in it["claims"]]

VALID_DIR = {"+", "-", "unclear", "absent"}

def parse_records(text):
    text = re.sub(r"^```[a-zA-Z]*\s*$", "", text, flags=re.M)  # strip fences
    text = text.strip()
    if text.startswith("["):  # whole-array response
        return json.loads(text)
    recs = []
    for ln in text.splitlines():
        ln = ln.strip().rstrip(",")
        if not ln or not ln.startswith("{"):
            continue
        recs.append(json.loads(ln))
    return recs

def main(folder):
    folder = Path(folder)
    if not folder.is_absolute():
        folder = HERE / folder
    errors, merged = [], {}
    for chunk, ids in MANIFEST["chunks"].items():
        f = folder / f"{chunk}.jsonl"
        if not f.exists():
            errors.append(f"MISSING FILE: {f.name} ({len(ids)} items)")
            continue
        try:
            recs = parse_records(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: unparseable JSON ({e})")
            continue
        seen = {}
        for r in recs:
            iid = r.get("item_id")
            if iid not in BATCH:
                errors.append(f"{f.name}: unknown item_id {iid!r}")
                continue
            seen[iid] = r
        for iid in ids:
            if iid not in seen:
                errors.append(f"{f.name}: item {iid} missing")
                continue
            r, want = seen[iid], BATCH[iid]
            got = [c.get("feature") for c in r.get("claims", [])]
            if sorted(got) != sorted(want):
                errors.append(f"{f.name}: {iid} features mismatch — want {want}, got {got}")
                continue
            clean = []
            for feat in want:  # canonical order
                c = next(c for c in r["claims"] if c["feature"] == feat)
                d = c.get("dir")
                if d not in VALID_DIR:
                    errors.append(f"{f.name}: {iid}/{feat}: bad dir {d!r}")
                    break
                hedged = bool(c.get("hedged", False)) and d in ("+", "-")
                clean.append({"feature": feat, "dir": d, "hedged": hedged})
            else:
                merged[iid] = {"item_id": iid, "claims": clean}
    print(f"parsed items: {len(merged)}/{len(BATCH)}   errors: {len(errors)}")
    for e in errors:
        print("  !", e)
    if errors:
        sys.exit(1)
    out = folder.parent / f"{folder.name}_merged.jsonl"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for iid in BATCH:  # batch order
            fh.write(json.dumps(merged[iid], ensure_ascii=False) + "\n")
    print(f"OK -> {out}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
