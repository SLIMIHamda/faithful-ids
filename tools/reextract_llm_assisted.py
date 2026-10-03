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
explanation texts are already in the batch file.

Since amendment 0005 the model is Google's QAT Q4_0 GGUF of Gemma-4-26B-A4B,
served by a local Ollama server (`model.runtime: ollama`). The Kaggle notebook
`kaggle/extractor_regate/` downloads the pinned file, checks its sha256, starts
Ollama and then calls this tool. Configs without `runtime: ollama` still load
through transformers.

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

# The providers' 160-token default is sized for generator prose. One extracted
# claim is ~25-30 tokens of JSON and 117/300 audit texts carry 5+ claims, so 160
# cuts the array short, the JSON fails to parse and the item silently falls
# back to the rule engine. 1024 holds the longest text (7 claims) many times.
EXTRACTION_MAX_NEW_TOKENS = 1024


def preflight(repo_id: str, headroom_gib: float) -> None:
    """Refuse to start unless the GPUs can actually hold the model.

    The first Kaggle attempt spent ~2.2 hours downloading ~50 GB of weights and
    THEN failed in ``validate_environment`` because ``device_map="auto"`` had
    spilled modules to CPU, which bnb-4bit rejects. The check costs a second and
    is worth having before the download, not after it.
    """
    try:
        import torch
    except Exception as exc:  # ImportError, but a broken install raises OSError
        print(f"preflight: torch unavailable ({type(exc).__name__}) — skipping the check")
        return
    if not torch.cuda.is_available():
        raise SystemExit(
            "preflight: no CUDA device. This needs a GPU session — on Kaggle set "
            "Accelerator to 'GPU T4 x2'."
        )
    n = torch.cuda.device_count()
    per = [torch.cuda.get_device_properties(i).total_memory / 2**30 for i in range(n)]
    usable = sum(max(0.0, g - headroom_gib) for g in per)
    names = ", ".join(f"{torch.cuda.get_device_name(i)} {per[i]:.1f}GiB" for i in range(n))
    print(f"preflight: {n} GPU(s) — {names}")
    print(f"preflight: usable after {headroom_gib} GiB/GPU headroom = {usable:.1f} GiB")
    # nf4 is ~0.55 bytes/param once quantisation constants and embeddings are
    # counted; 26B -> ~14.5 GiB, plus room for activations and the KV cache.
    need = 16.0
    if usable < need:
        raise SystemExit(
            f"preflight: {usable:.1f} GiB usable is below the ~{need:.0f} GiB "
            f"that {repo_id} needs in nf4. "
            "On Kaggle set Accelerator to 'GPU T4 x2' (2 x 16 GiB) — a single "
            "T4 or P100 cannot hold this model. Or lower the reserve with "
            "FAITHFULIDS_GPU_HEADROOM_GIB=1.0. Refusing to download ~50 GB of "
            "weights that cannot then be loaded."
        )


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
    elif cfg["model"].get("runtime") == "ollama":
        # Amendment 0005: pinned GGUF on a running Ollama server; Ollama places
        # layers across GPUs itself, so the nf4 preflight does not apply.
        from faithfulids.llm.providers import OllamaProvider

        client = LLMClient(OllamaProvider(max_new_tokens=EXTRACTION_MAX_NEW_TOKENS),
                           ledger, mode="live")
    else:
        import os as _os

        from faithfulids.llm.providers import TransformersProvider

        preflight(cfg["model"]["weights"]["hf_repo"],
                  float(_os.environ.get("FAITHFULIDS_GPU_HEADROOM_GIB", "2.0")))
        client = LLMClient(TransformersProvider(max_new_tokens=EXTRACTION_MAX_NEW_TOKENS),
                           ledger, mode="live")
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
