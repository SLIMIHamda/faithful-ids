"""Analysis runner (repository boundary A) — a pure consumer of runs/**.

Loads metric rows through the READ-ONLY results API (``faithfulids.results``),
runs a pre-registered test named by the analysis config, and writes a manifested
output directory. The deterministic ``results.json`` carries the numbers; the
``MANIFEST.json`` carries provenance (the exact run ids + timestamp). Analysis
enumerates run ids — no globbing over runs (hostile-audit A7). It never imports
``orchestration``/``generation``/``llm`` (edge 4).

Run: ``python -m analysis.run --config <name>`` | ``--all`` | ``--all --check``
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from analysis.src.bootstrap_ci import bootstrap_mean_ci
from analysis.src.coverage_risk import risk_coverage_curve
from analysis.src.friedman_nemenyi import friedman_nemenyi
from faithfulids.provenance import repo_root, sha256_json, sha256_text
from faithfulids.results.api import ResultError, list_runs, load_metrics

CONFIG_DIR = repo_root() / "analysis" / "configs"
OUTPUT_DIR = repo_root() / "analysis" / "outputs"


def load_config(name: str) -> dict:
    return yaml.safe_load((CONFIG_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def _resolve_run_ids(cfg: dict, runs_root) -> list[str]:
    if "run_ids" in cfg:
        if cfg["run_ids"]:
            return list(cfg["run_ids"])
        raise ResultError(
            f"{cfg.get('id')}: run_ids not yet enumerated (experiment pending execution)"
        )
    src = cfg.get("source") or {}
    if src.get("select") == "latest":
        runs = list_runs(src["experiment"], runs_root)
        if not runs:
            raise ResultError(f"no runs available for {src['experiment']}")
        return [sorted(runs)[-1]]
    raise ValueError(f"analysis config {cfg.get('id')} must give run_ids or source.select")


def _instance_values(rows, metric, generator, *, gate_metric=None):
    """Per-instance ``metric`` values for one generator, sorted by instance id.

    ``gate_metric`` implements NaN-exclusion aggregation (2026-07-14): instances
    where the gate metric is 0 are DROPPED because the target metric is *undefined*
    there, not zero. The motivating case is ``dsa_asserted`` gated on
    ``direction_assertion_rate`` — an instance that asserts no directions returns a
    structural ``dsa_asserted`` of 0.0; averaging those in pulls a confirmatory
    reading-fidelity mean toward the fraction of silent instances rather than
    measuring reading fidelity. A genuinely all-wrong instance keeps
    ``direction_assertion_rate > 0`` and stays in, so real failures are not hidden."""
    def _by_instance(m):
        return {
            r["instance_id"]: r["value"] for r in rows
            if r["layer"] == "layer1" and r["metric"] == m
            and r["grouping"].get("generator_id") == generator
        }
    vals = _by_instance(metric)
    if gate_metric is not None:
        gate = _by_instance(gate_metric)
        return [v for inst, v in sorted(vals.items()) if gate.get(inst, 0.0) > 0.0]
    return [v for _, v in sorted(vals.items())]


def _layer1_matrix(rows, metric, generators):
    instances = sorted(
        {r["instance_id"] for r in rows if r["layer"] == "layer1" and r["metric"] == metric}
    )
    matrix = []
    for g in generators:
        line = []
        for inst in instances:
            vals = [
                r["value"] for r in rows
                if r["layer"] == "layer1" and r["metric"] == metric
                and r["instance_id"] == inst and r["grouping"].get("generator_id") == g
            ]
            line.append(vals[0] if vals else 0.0)
        matrix.append(line)
    return matrix, instances


def build_result(name: str, runs_root=None) -> tuple[dict, list[str]]:
    cfg = load_config(name)
    run_ids = _resolve_run_ids(cfg, runs_root)
    rows: list[dict] = []
    for rid in run_ids:
        rows.extend(load_metrics(rid, runs_root))

    test = cfg["test"]
    if test == "friedman_nemenyi":
        matrix, instances = _layer1_matrix(rows, cfg["metric"], cfg["generators"])
        result = friedman_nemenyi(matrix, higher_is_better=cfg.get("higher_is_better", True))
        result.update({"metric": cfg["metric"], "methods": cfg["generators"], "scores": matrix})
    elif test == "mean_ci":
        gate = cfg.get("gate_metric")  # e.g. direction_assertion_rate for dsa_asserted
        per, n_kept = {}, {}
        for g in cfg["generators"]:
            vals = _instance_values(rows, cfg["metric"], g, gate_metric=gate)
            n_kept[g] = len(vals)
            per[g] = bootstrap_mean_ci(vals, seed=cfg.get("seed", 0)) if vals else None
        result = {"metric": cfg["metric"], "gate_metric": gate,
                  "n_instances": n_kept, "per_generator": per}
    elif test == "coverage_risk":
        g = cfg["generator"]
        metric = cfg["metric"]
        per_inst = sorted(
            (r["instance_id"], r["value"]) for r in rows
            if r["layer"] == "layer1" and r["metric"] == metric
            and r["grouping"].get("generator_id") == g
        )
        # risk = 1 - faithfulness; confidence proxy = faithfulness score
        risks = [1.0 - v for _, v in per_inst]
        confidences = [v for _, v in per_inst]
        result = risk_coverage_curve(risks, confidences)
        result.update({"metric": metric, "generator": g})
    else:
        raise ValueError(f"unknown analysis test: {test!r}")
    return {"analysis": name, "hypothesis": cfg.get("hypothesis"), "result": result}, run_ids


def _round_floats(obj, ndigits: int = 10):
    """Round floats so results.json is byte-stable across platforms (last-bit
    float noise from scipy/numpy would otherwise break the stats-regen diff)."""
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, list):
        return [_round_floats(x, ndigits) for x in obj]
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    return obj


def _results_json(payload: dict) -> str:
    return json.dumps(_round_floats(payload), indent=2, sort_keys=True) + "\n"


def write_output(name: str, runs_root=None) -> Path:
    payload, run_ids = build_result(name, runs_root)
    out = OUTPUT_DIR / name
    out.mkdir(parents=True, exist_ok=True)
    body = _results_json(payload)
    (out / "results.json").write_text(body, encoding="utf-8")
    manifest = {
        "analysis": name,
        "run_ids": run_ids,
        "results_sha256": sha256_text(body),
        "config_sha256": sha256_json(load_config(name)),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def check_output(name: str, runs_root=None) -> bool:
    """Regenerate results.json content and compare to the committed copy."""
    payload, _ = build_result(name, runs_root)
    committed = OUTPUT_DIR / name / "results.json"
    if not committed.is_file():
        return False
    return committed.read_text(encoding="utf-8") == _results_json(payload)


def _all_configs() -> list[str]:
    return sorted(p.stem for p in CONFIG_DIR.glob("*.yaml"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="analysis.run")
    parser.add_argument("--config")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    names = _all_configs() if args.all else ([args.config] if args.config else [])
    if not names:
        parser.error("provide --config <name> or --all")

    problems = 0
    for name in names:
        try:
            if args.check:
                ok = check_output(name, None)
                print(f"{name}: {'OK (matches committed)' if ok else 'MISMATCH'}")
                problems += 0 if ok else 1
            else:
                out = write_output(name, None)
                print(f"{name}: wrote {out}")
        except ResultError as exc:
            # runs not available yet (e.g. real experiments not executed) -> pending
            print(f"{name}: pending — {exc}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
