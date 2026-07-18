#!/usr/bin/env python3
"""Token-free re-score of a completed pilot run (L5 / L3).

Re-runs the pilot vertical slice in **replay** mode: the detector is retrained
(deterministic) and TreeSHAP recomputed, but every LLM generation is served from
the original run's ledger instead of the model — so no GPU is used and no tokens
are spent. The point is to recompute Layer-1/Layer-2 with the CURRENT extractor /
metric code (e.g. after the Pass B extractor bump to 1.1.0) and get a fresh,
comparable run whose numbers finally match the fixed instruments.

A replay cache miss is a hard error, so the environment MUST reproduce the
original run's instances byte-for-byte:

    FAITHFULIDS_DATA_DIR    the same CICIDS2017 CSV directory
    FAITHFULIDS_PILOT_N     the same N as the original run (e.g. 150)
    FAITHFULIDS_MAX_ROWS    the same row cap (binary runs; unset for K-way)
    FAITHFULIDS_ROWS_PER_FILE  the same per-file cap (K-way runs, e.g. 50000)
    FAITHFULIDS_PILOT_DETECTOR the same detector config id if overridden
                               (K-way runs: xgboost_multiclass)
    FAITHFULIDS_PILOT_LLM   the same generator LLM id (e.g. qwen3_8b_4bit)
    FAITHFULIDS_LLM_CACHE_DIR  the ledger dir from the original run's artifacts
                               (…/runs/_pilot_llm_cache); defaults to runs/_pilot_llm_cache
    FAITHFULIDS_PILOT_GENERATORS  the ORIGINAL run's generator list (comma-
                               separated; see its resolved_config). Required for
                               runs generated before b5_narrative_vte joined the
                               axis — a b5 cell has no ledger entries there:
                               b0_raw_shap,b1_template,b2_zeroshot,b3_dte_style,b4_vte

Usage:  PYTHONPATH=src python tools/rescore_run.py [--experiment EXP-PILOT-001]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from faithfulids.orchestration.execute import run_pilot
from faithfulids.provenance import repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rescore_run")
    parser.add_argument("--experiment", default="EXP-PILOT-001")
    args = parser.parse_args(argv)

    data_dir = os.environ.get("FAITHFULIDS_DATA_DIR")
    if not data_dir:
        print("ERROR: set FAITHFULIDS_DATA_DIR to the CICIDS2017 CSV directory.", file=sys.stderr)
        return 2

    runs_root = repo_root() / "runs"
    cache_dir = os.environ.get("FAITHFULIDS_LLM_CACHE_DIR") or (runs_root / "_pilot_llm_cache")
    if not (Path(cache_dir) / "ledger.jsonl").is_file():
        print(
            f"ERROR: no ledger at {cache_dir}/ledger.jsonl — replay needs the original run's "
            "cached generations. Point FAITHFULIDS_LLM_CACHE_DIR at the downloaded "
            "runs/_pilot_llm_cache from the run you are re-scoring.",
            file=sys.stderr,
        )
        return 2

    n = os.environ.get("FAITHFULIDS_PILOT_N")
    max_rows = os.environ.get("FAITHFULIDS_MAX_ROWS")
    rows_per_file = os.environ.get("FAITHFULIDS_ROWS_PER_FILE")
    llm_override = os.environ.get("FAITHFULIDS_PILOT_LLM") or None
    detector_override = os.environ.get("FAITHFULIDS_PILOT_DETECTOR") or None
    gens = os.environ.get("FAITHFULIDS_PILOT_GENERATORS") or None
    gens_override = [g.strip() for g in gens.split(",") if g.strip()] if gens else None

    run_dir = run_pilot(
        args.experiment,
        data_dir=data_dir,
        runs_root=runs_root,
        n_explain=int(n) if n else None,
        max_rows=int(max_rows) if max_rows else None,
        rows_per_file=int(rows_per_file) if rows_per_file else None,
        llm_id_override=llm_override,
        detector_id_override=detector_override,
        generator_ids_override=gens_override,
        enforce_competence=False,  # re-score is a measurement pass, not a gate
        llm_mode="replay",
        llm_cache_dir=cache_dir,
    )
    print(f"re-scored run (replay, extractor re-applied): {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
