#!/usr/bin/env python3
"""Re-extract an audit batch through the extractor's LLM-ASSISTED path.

Every EXP-G-001 attempt so far has scored the extractor's **rule-only fallback**.
`configs/extraction/eval_extractor.yaml` registers `rule_assisted: true` with a
pinned model (`google/gemma-4-26B-A4B-it`), and `RuleAssistedExtractor.extract`
uses the regex engine only when no LLM client is supplied — which is what the
pilot does, for GPU economy. So the gate has been auditing the degraded mode of
the registered instrument.

This runs the registered instrument. It needs a GPU and the extractor model, but
**nothing else**: no dataset, no detector, no SHAP, no generator tokens. The 300
explanation texts are already in the batch file. On Kaggle that is one 2xT4
session; the model is ~14 GB in nf4 and needs `FAITHFULIDS_DEVICE_MAP=auto`.

Gemma 4 requires transformers v5.x, while generator sessions are pinned <5 — so
this must run in its OWN session with `pip install -U transformers`.

Every call goes through the ledger, so the extraction is replayable afterwards
without the GPU: re-scoring never needs to re-run the model.

Run::

    python tools/reextract_llm_assisted.py --batch experiments/gates/EXP-G-001_audit_v2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from faithfulids.extraction import build as build_extractor  # noqa: E402
from faithfulids.framework import ExplanationRecord  # noqa: E402
from faithfulids.llm import CallLedger, LLMClient  # noqa: E402
from faithfulids.orchestration.config_loader import load_config  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, default=None,
                    help="call-ledger dir (default: <batch>/_llm_extraction_cache)")
    ap.add_argument("--mode", choices=("live", "replay"), default="live",
                    help="replay re-parses from the ledger with NO model and NO GPU")
    ap.add_argument("--limit", type=int, help="first N items only (smoke test)")
    args = ap.parse_args(argv)

    batch = args.batch
    items = [json.loads(line) for line in
             (batch / "audit_batch.jsonl").read_text(encoding="utf-8").splitlines()
             if line.strip()]
    if args.limit:
        items = items[:args.limit]
    key_path = batch / "audit_key_DO_NOT_SHOW_ANNOTATOR.json"
    key = json.loads(key_path.read_text(encoding="utf-8"))
    vocab = sorted(json.loads((batch / "feature_vocabulary.json").read_text(encoding="utf-8")))

    cfg = load_config("extraction", "eval_extractor")
    version = cfg["version"]
    ledger = CallLedger(args.ledger or (batch / "_llm_extraction_cache"))
    if args.mode == "replay":
        client = LLMClient(None, ledger, mode="replay")
    else:
        from faithfulids.llm.providers import TransformersProvider

        client = LLMClient(TransformersProvider(), ledger, mode="live")
    model = {**cfg["model"], "id": cfg["id"]}
    ext = build_extractor(cfg, llm_client=client, model_config=model,
                          feature_vocabulary=vocab)

    print(f"extractor {version} (LLM-assisted, {args.mode}) over {len(items)} texts")
    ev, t0, fell_back = Counter(), time.time(), 0
    for n, it in enumerate(items, 1):
        iid = it["item_id"]
        claims = ext.extract(ExplanationRecord(
            iid, key[iid]["generator_id"], it["explanation_text"])).claims
        for c in claims:
            ev[c.direction_evidence] += 1
        # "llm" evidence means the model's JSON was parsed; anything else means
        # the rule engine handled that claim, i.e. the LLM path did not answer.
        if claims and not any(c.direction_evidence == "llm" for c in claims):
            fell_back += 1
        key[iid][f"extractor_claims_{version.replace('.', '_')}_llm"] = [
            {k: v for k, v in c.to_dict().items()
             if k in ("feature", "direction", "direction_evidence")} for c in claims
        ]
        if n == 1 or n % 25 == 0 or n == len(items):
            print(f"  [{n}/{len(items)}] {(time.time() - t0) / n:.1f}s/item", flush=True)

    key_path.write_text(json.dumps(key, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                        encoding="utf-8")
    total = sum(ev.values())
    print(f"\nclaims: {total}   evidence: {dict(ev.most_common())}")
    print(f"items where the LLM path produced nothing and the rules took over: "
          f"{fell_back}/{len(items)}")
    if fell_back == len(items):
        print("\nWARNING: the LLM path never answered — every item fell back to the rule\n"
              "engine, so this run scores the SAME instrument as before. Check the model\n"
              "loaded, and that its replies parse as the JSON the prompt asks for.")
    print(f"\nwrote claims to {key_path.name} under "
          f"'extractor_claims_{version.replace('.', '_')}_llm'")
    print(f"score with:  python tools/score_audit_gate.py --batch {batch.as_posix()} "
          f"--pass LLM_1_V2 --pass LLM_2_V2 "
          f"--claims-key extractor_claims_{version.replace('.', '_')}_llm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
