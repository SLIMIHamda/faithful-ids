"""The orchestration CLI (L5). The runner accepts exactly one argument: an
experiment id. Everything else is resolved from the registry + snapshot.

``make run EXP=<id>`` -> ``faithfulids run --experiment <id>``.
"""

from __future__ import annotations

import argparse
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

    # Real experiments: enforce gates, then execute. Full execution requires
    # acquired datasets + frozen models + a live/replay LLM — this artifact ships
    # the machine, not the runs. Fail loudly rather than fabricate outputs.
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
