"""The orchestration CLI (L5). The runner accepts exactly one argument: an
experiment id. Everything else is resolved from the registry + snapshot.

``make run EXP=<id>`` -> ``faithfulids run --experiment <id>``.
"""

from __future__ import annotations

import argparse
import os
import sys

from faithfulids.orchestration.gates import enforce_gates
from faithfulids.orchestration.registry import load_experiment
from faithfulids.provenance import repo_root


def cmd_run(args: argparse.Namespace) -> int:
    exp = load_experiment(args.experiment)
    runs_root = repo_root() / "runs"

    if exp["tier"] == "toy":
        from faithfulids.orchestration.toy_pipeline import run_toy

        run_dir = run_toy(runs_root)
        print(f"toy run complete (NON-CITABLE): {run_dir}")
        return 0

    if exp["tier"] in ("pilot", "tier_a"):
        # Real vertical slice on real data (CICIDS2017 CSVs mounted at
        # $FAITHFULIDS_DATA_DIR). The pilot has no gate dependencies; Tier-A
        # experiments declare EXP-G-001/EXP-G-002 and enforce_gates below
        # refuses to score until PASSED gate runs exist under runs/. One LLM per
        # run (Kaggle memory): the launcher loops FAITHFULIDS_PILOT_LLM over
        # the experiment's roster; N comes from the experiment's sampling ref.
        from faithfulids.orchestration.execute import run_pilot

        data_dir = os.environ.get("FAITHFULIDS_DATA_DIR")
        if not data_dir:
            print(
                "ERROR: set FAITHFULIDS_DATA_DIR to the CICIDS2017 CSV directory "
                "(e.g. a mounted Kaggle dataset). See kaggle/README.md.",
                file=sys.stderr,
            )
            return 2
        # Tier-A runs in two steps (a generator and the registered extractor do
        # not fit one 2x T4 session): "generate" fills the ledger with the
        # generator LLM, resumably; "score" replays it, extracts with the
        # extractor EXP-G-001 certifies, computes the metrics, writes the run.
        phase = None
        tier_kwargs: dict = {}
        if exp["tier"] == "tier_a":
            phase = os.environ.get("FAITHFULIDS_PHASE")
            if phase not in ("generate", "score"):
                print(
                    "ERROR: Tier-A runs in two steps. Set FAITHFULIDS_PHASE=generate "
                    "(the generator LLM fills the ledger; repeat until it reports "
                    "COMPLETE), then FAITHFULIDS_PHASE=score (replay, LLM extraction, "
                    "metrics, run). See kaggle/tier_a/.",
                    file=sys.stderr,
                )
                return 2
            budget = os.environ.get("FAITHFULIDS_GENERATION_BUDGET_MIN")
            tier_kwargs = dict(
                llm_cache_dir=os.environ.get("FAITHFULIDS_LLM_CACHE_DIR")
                or runs_root / "_tier_a_llm_cache",
                extraction_cache_dir=os.environ.get("FAITHFULIDS_EXTRACTION_CACHE_DIR")
                or runs_root / "_tier_a_extraction_cache",
                # score step only: the phi verifier (amendment 0008) and the
                # plausibility judge (amendment 0009), each on its own ledger
                verifier_cache_dir=os.environ.get("FAITHFULIDS_VERIFIER_CACHE_DIR")
                or runs_root / "_tier_a_verifier_cache",
                judge_cache_dir=os.environ.get("FAITHFULIDS_JUDGE_CACHE_DIR")
                or runs_root / "_tier_a_judge_cache",
                **({"extraction": "none", "llm_mode": "live",
                    "generation_budget_s": float(budget) * 60 if budget else None}
                   if phase == "generate" else {"extraction": "llm", "llm_mode": "replay"}),
            )
        # Gates guard metric computation; the generate step computes none.
        if phase != "generate":
            enforce_gates(exp, runs_root)
        n = os.environ.get("FAITHFULIDS_PILOT_N")
        max_rows = os.environ.get("FAITHFULIDS_MAX_ROWS")
        # Per-FILE row cap (evenly-spaced subsample): unlike the global MAX_ROWS —
        # which appends whole files in name order and so keeps only the first
        # day's attack families — every day survives. REQUIRED for the K-way
        # detector to see all canonical classes under a memory cap.
        rows_per_file = os.environ.get("FAITHFULIDS_ROWS_PER_FILE")
        # Per-run generator LLM (scale test: run once per model, compare b2 across).
        llm_override = os.environ.get("FAITHFULIDS_PILOT_LLM") or None
        # Per-run detector config (queue #5.6): select the K-way detector
        # (xgboost_multiclass) instead of the binary attack-vs-benign collapse.
        detector_override = os.environ.get("FAITHFULIDS_PILOT_DETECTOR") or None
        # Comma-separated generator-axis override. Main use: REPLAY re-scores of
        # runs generated before b5 joined the axis (pin the original list).
        # Layer-2 removal semantics (invariance check): 'conditional' (default) or
        # 'background'. Re-scoring a run under both bounds how much the Layer-2
        # conclusions depend on the erasure operator rather than on the claims.
        erasure_op = os.environ.get("FAITHFULIDS_ERASURE_OPERATOR") or None
        gens = os.environ.get("FAITHFULIDS_PILOT_GENERATORS") or None
        gens_override = [g.strip() for g in gens.split(",") if g.strip()] if gens else None
        # Competence gate on by default; set FAITHFULIDS_ENFORCE_COMPETENCE=0 to
        # REPORT the per-family table without halting (exploratory pilot).
        enforce = os.environ.get("FAITHFULIDS_ENFORCE_COMPETENCE", "1") != "0"
        from faithfulids.llm import ReplayMiss

        try:
            run_dir = run_pilot(
                exp["id"], data_dir=data_dir, runs_root=runs_root,
                n_explain=int(n) if n else None,
                max_rows=int(max_rows) if max_rows else None,
                rows_per_file=int(rows_per_file) if rows_per_file else None,
                llm_id_override=llm_override,
                detector_id_override=detector_override,
                generator_ids_override=gens_override,
                erasure_operator=erasure_op,
                enforce_competence=enforce,
                **tier_kwargs,
            )
        except ReplayMiss as exc:
            if phase != "score":
                raise
            print(f"ERROR: the generation ledger is incomplete for this model ({exc}). "
                  "Run FAITHFULIDS_PHASE=generate until it reports COMPLETE, with the "
                  "same model, N, data and FAITHFULIDS_LLM_CACHE_DIR.", file=sys.stderr)
            return 4
        if run_dir is None:
            print("generate step finished; no run is written until the score step")
            return 0
        print(f"{'Tier-A' if phase else 'pilot'} run complete: {run_dir}")
        return 0

    if exp["id"] == "EXP-G-002":
        # RQ0 metric calibration: token-free and LLM-free (B1 is deterministic;
        # corruptions are claim-level), needs only data + the detector. Runs on
        # Kaggle against the K-way detector by default (calibrates Layer-2 on
        # the Tier-A regime); FAITHFULIDS_PILOT_DETECTOR overrides.
        from faithfulids.orchestration.rq0_gate import run_rq0_gate

        data_dir = os.environ.get("FAITHFULIDS_DATA_DIR")
        if not data_dir:
            print("ERROR: set FAITHFULIDS_DATA_DIR to the CICIDS2017 CSV directory.",
                  file=sys.stderr)
            return 2
        n = os.environ.get("FAITHFULIDS_PILOT_N")
        max_rows = os.environ.get("FAITHFULIDS_MAX_ROWS")
        rows_per_file = os.environ.get("FAITHFULIDS_ROWS_PER_FILE")
        run_dir = run_rq0_gate(
            exp["id"], data_dir=data_dir, runs_root=runs_root,
            n_instances=int(n) if n else None,
            max_rows=int(max_rows) if max_rows else None,
            rows_per_file=int(rows_per_file) if rows_per_file else None,
            detector_id_override=os.environ.get("FAITHFULIDS_PILOT_DETECTOR") or None,
        )
        from faithfulids.provenance import read_manifest

        print(f"RQ0 gate run complete: {run_dir} — gate {read_manifest(run_dir).gate}")
        return 0

    # Other real experiments (Tier A/B/…): enforce gates, then execute. Full
    # execution requires acquired datasets + frozen models + a live/replay LLM —
    # not yet wired. Fail loudly rather than fabricate outputs.
    enforce_gates(exp, runs_root)
    print(
        f"ERROR: full execution of {args.experiment!r} requires acquired datasets, "
        "frozen detector artifacts, and a live-or-replay LLM provider "
        "(see REPRODUCING.md). No dataset is downloaded and no LLM is called by "
        "this infrastructure build.",
        file=sys.stderr,
    )
    return 3


def cmd_replay(args: argparse.Namespace) -> int:
    print(
        f"replay tier {args.tier}: cache-only replay recomputes metrics from the "
        "LLM ledger without network/GPU. Requires released caches + run artifacts "
        "(see REPRODUCING.md L3).",
        file=sys.stderr,
    )
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="faithfulids")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="execute a registered experiment")
    run_p.add_argument("--experiment", required=True)
    replay_p = sub.add_parser("replay", help="cache-only replay (L3)")
    replay_p.add_argument("--tier", default="L3")
    args = parser.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "replay":
        return cmd_replay(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
