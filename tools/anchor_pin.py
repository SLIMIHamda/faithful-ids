#!/usr/bin/env python3
"""Resolve a generator's PINNED revision, and format its lm-eval scores.

Two jobs for the capability-anchor cell, kept in the repo rather than inlined in
the notebook so both are testable and reviewable:

* with no ``--results``: print ``<hf_repo> <revision>`` for the given LLM config,
  so the harness measures the exact revision the experiment generates with. An
  anchor taken from a different revision measures a different model.
* with ``--results <dir>``: read the harness output and print the YAML row to
  paste into ``analysis/data/capability_anchor.yaml``.

Scores are never invented: a task the harness did not report comes out ``null``,
and the anchor file's contract is that null means *not yet measured*.

Run::

    python tools/anchor_pin.py qwen3_4b_4bit
    python tools/anchor_pin.py qwen3_4b_4bit --results /kaggle/working/anchor_qwen3_4b_4bit
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import yaml  # noqa: E402


def pins(llm_id: str) -> tuple[str, str]:
    cfg = yaml.safe_load((REPO / "configs" / "llms" / f"{llm_id}.yaml").read_text(encoding="utf-8"))
    w = cfg.get("weights") or {}
    if not w.get("hf_repo") or not w.get("revision"):
        raise SystemExit(
            f"{llm_id} has no pinned open weights (provider {cfg.get('provider')!r}). "
            "The capability anchor measures pinned revisions only."
        )
    return w["hf_repo"], w["revision"]


def _pick(results: dict, task: str, *prefixes: str):
    d = results.get(task) or {}
    for p in prefixes:
        for k, v in d.items():
            if k.startswith(p) and isinstance(v, (int, float)):
                return round(float(v), 4)
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("llm_id")
    ap.add_argument("--results", type=Path, help="lm-eval --output_path directory")
    args = ap.parse_args(argv)

    repo_id, rev = pins(args.llm_id)
    if not args.results:
        print(f"{repo_id} {rev}")
        return 0

    found = sorted(glob.glob(str(args.results / "**" / "results*.json"), recursive=True))
    if not found:
        raise SystemExit(f"no lm-eval results*.json under {args.results} — check the run for errors")
    results = json.loads(Path(found[-1]).read_text(encoding="utf-8")).get("results", {})
    mmlu = _pick(results, "mmlu", "acc,", "acc")
    ifeval = _pick(results, "ifeval", "prompt_level_strict_acc", "inst_level_strict_acc")
    limit = os.environ.get("MMLU_LIMIT", "?")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    src = f"lm-eval harness, mmlu+ifeval, limit={limit} per subject, 4bit, {stamp}"
    print(f"  - llm: {args.llm_id}")
    print(f"    hf_repo: {repo_id}")
    print(f"    revision: {rev}")
    print(f"    mmlu: {'null' if mmlu is None else mmlu}")
    print(f"    ifeval: {'null' if ifeval is None else ifeval}")
    print(f'    capability_source: "{src}"')
    if mmlu is None or ifeval is None:
        print("\n# WARNING: a null above means the harness reported no score for that task.",
              "\n# Leave it null rather than substituting a published number — the anchor's",
              "\n# whole point is that all four rows come from ONE harness run.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
