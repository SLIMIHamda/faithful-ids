#!/usr/bin/env python3
"""Send the drafts a verifier already judged to the CURRENT pinned verifier (amendment 0010).

Amendment 0010 replaced Phi-4-mini with Phi-4 (14B) after Phi-4-mini rejected all
40 drafts of the 2026-10-03 score smoke run, with reasons false on their face. It
allows one more attempt, decided on **the same drafts**. Those drafts cannot be
regenerated (taxonomy 3.0.0 changed the detector, so the old prompts no longer
come out of the pipeline), but the old verifier ledger stores every full verifier
prompt: evidence list plus draft, filled from the frozen prompt `b4_vte/verifier`
1.0.0. This tool sends each stored prompt, with its stored params, to the model
`b4_vte.yaml` now pins, through a new ledger, and writes a review sheet.

The review sheet (``review.csv``, one row per distinct draft) is what the author
marks: for each rejection, is every stated reason false (a feature called absent
that is in the evidence, a direction the draft does not state, a magnitude called
invented where the draft states none)? Amendment 0010(B) turns the count into the
decision.

Needs the verifier model on a local Ollama server (``kaggle/verifier_recheck/``
sets that up). ``--mode replay`` re-reads the new ledger without the model.

Run::

    python tools/recheck_verifier.py --old-ledger <dir> --out <dir> [--mode replay]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from faithfulids.generation.b4_vte.verifier.verifier import read_verdict  # noqa: E402
from faithfulids.orchestration.config_loader import load_config  # noqa: E402
from faithfulids.orchestration.execute import instrument_client, instrument_model  # noqa: E402

_EVIDENCE = "Evidence — ranked feature attributions:"
_DRAFT = "Draft explanation under review:"
_TAIL = "For the draft, judge each of the following"


def split_prompt(prompt: str) -> tuple[str, str]:
    """(evidence list, draft) out of a filled b4_vte/verifier 1.0.0 prompt."""
    if _EVIDENCE not in prompt or _DRAFT not in prompt or _TAIL not in prompt:
        raise ValueError("not a b4_vte/verifier 1.0.0 prompt")
    evidence = prompt.split(_EVIDENCE, 1)[1].split(_DRAFT, 1)[0].strip()
    draft = prompt.split(_DRAFT, 1)[1].split(_TAIL, 1)[0].strip()
    return evidence, draft


def recheck(old_ledger: Path, out: Path, *, mode: str = "live", provider=None) -> dict:
    old = [json.loads(line) for line in
           (old_ledger / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    vcfg = load_config("generator", "b4_vte")["verifier"]
    model = instrument_model(vcfg)
    client = instrument_client(model, out / "ledger", mode=mode, provider=provider)
    rows = []
    for i, rec in enumerate(old, 1):
        evidence, draft = split_prompt(rec["prompt"])
        resp = client.complete(model_config=model, prompt=rec["prompt"], params=rec["params"])
        old_ok, old_reason = read_verdict(rec["response_text"])
        new_ok, new_reason = read_verdict(resp.text)
        rows.append({
            "item": i, "evidence": evidence, "draft": draft,
            "old_model": rec["model_id"], "old_verdict": old_reason, "old_reply": rec["response_text"],
            "new_model": model["id"], "new_verdict": new_reason, "new_reply": resp.text,
            # filled in by the author, per amendment 0010(B)
            "author_reasons_checked": "", "author_rejection_wrong": "",
        })
        print(f"  [{i}/{len(old)}] {old_reason} -> {new_reason}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = {
        "old_model": old[0]["model_id"] if old else None, "new_model": model["id"],
        "new_weights": dict(model["weights"]), "n_drafts": len(rows),
        "old_verdicts": dict(Counter(r["old_verdict"] for r in rows)),
        "new_verdicts": dict(Counter(r["new_verdict"] for r in rows)),
        "rule": "amendment 0010(B): unusable if more than half of the new rejections are wrong",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--old-ledger", type=Path, required=True,
                    help="folder holding the earlier verifier's ledger.jsonl")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", choices=("live", "replay"), default="live")
    args = ap.parse_args(argv)
    summary = recheck(args.old_ledger, args.out, mode=args.mode)
    print(json.dumps(summary, indent=2))
    print(f"\nreview sheet: {args.out / 'review.csv'} (mark each rejection, amendment 0010(B))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
