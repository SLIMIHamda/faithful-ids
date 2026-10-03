"""EXP-G-001 gate run (L5): turn a scored extractor audit into the gate token.

``tools/score_audit_gate.py`` scores the audit (amendment 0004's rule, both
annotator passes, both adjudication extremes). With ``--write-run`` it hands its
verdict here, and this writes ``runs/EXP-G-001/<run_id>/`` the way EXP-G-002
does: a write-once run whose manifest carries ``gate: PASSED`` or ``FAILED``.
``orchestration.gates`` reads that token before any experiment that declares
EXP-G-001.

The token certifies ONE instrument: the registered extractor at its current
version, through its LLM path. Attempts 1-4 scored the rule-only fallback, which
is not the registered instrument (amendment 0005), so a token is refused for any
claims but ``extractor_claims_<version>_llm``. The run records that version, and
``enforce_gates`` accepts a G-001 token only for the version the dependent
experiment's extraction config declares: changing the extractor needs a new
gate run.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from faithfulids.framework import ClaimSet, ClaimTuple, Direction, ExplanationRecord
from faithfulids.orchestration.runner import CellArtifacts, write_run
from faithfulids.provenance import (
    ArtifactRef,
    CodeVersion,
    ModelRef,
    mint_run_id,
    repo_root,
    sha256_file,
    sha256_json,
)

GATE_ID = "EXP-G-001"


def llm_claims_key(version: str) -> str:
    """The audit-key field holding the LLM path's claims for extractor ``version``."""
    return f"extractor_claims_{version.replace('.', '_')}_llm"


def _ref(path: Path, kind: str) -> ArtifactRef:
    try:
        name = path.resolve().relative_to(repo_root()).as_posix()
    except ValueError:
        name = path.name
    return ArtifactRef(name, sha256_file(path), kind=kind)


def write_extractor_gate_run(
    runs_root: str | Path,
    *,
    batch: Path,
    items: Mapping[str, Mapping[str, Any]],
    key: Mapping[str, Mapping[str, Any]],
    claims_key: str,
    extractor_cfg: Mapping[str, Any],
    verdict: Mapping[str, Any],
    pass_files: Sequence[Path],
    adjudication: Path | None,
    code_version: CodeVersion,
    now: datetime | None = None,
) -> Path:
    """Write the EXP-G-001 run for a scored audit and return its directory.

    ``verdict`` is the payload ``score_audit_gate.py`` writes to
    ``gate_result.json``; ``items`` the audit batch keyed by item id; ``key``
    the audit key holding ``claims_key``.
    """
    version = str(extractor_cfg["version"])
    if claims_key != llm_claims_key(version):
        raise ValueError(
            f"a gate token certifies the registered extractor {version} through its "
            f"LLM path, i.e. claims under {llm_claims_key(version)!r}; got {claims_key!r}"
        )
    if verdict.get("sensitivity_only"):
        raise ValueError("a sensitivity score (--exclude-first) is never the verdict")

    art = CellArtifacts()
    prompt_sha = extractor_cfg["prompt"]["sha256"]
    for iid, it in items.items():
        art.explanations.append(
            ExplanationRecord(iid, key[iid]["generator_id"], it["explanation_text"])
        )
        art.claims.append(ClaimSet(
            instance_id=iid,
            claims=tuple(
                ClaimTuple(
                    feature=c["feature"],
                    direction=Direction.from_str(c["direction"]) if c["direction"] else None,
                    direction_evidence=c["direction_evidence"],
                )
                for c in key[iid][claims_key]
            ),
            extractor_id=extractor_cfg["id"], extractor_version=version,
            prompt_sha256=prompt_sha,
        ))

    for label, r in verdict["results"].items():
        for metric in ("precision", "recall", "f1"):
            art.metric_rows.append({
                "instance_id": "__aggregate__", "layer": "gate", "metric": metric,
                "value": float(r[metric]),
                "grouping": {"gold_resolution": label, "tp": r["tp"],
                             "n_gold": r["n_gold"], "n_pred": r["n_pred"]},
            })
    for metric in ("agreement", "cohens_kappa", "krippendorff_alpha"):
        if verdict.get(metric) is not None:
            art.metric_rows.append({
                "instance_id": "__aggregate__", "layer": "gate_annotation",
                "metric": metric, "value": float(verdict[metric]), "grouping": {},
            })
    art.metric_rows.append({
        "instance_id": "__aggregate__", "layer": "gate", "metric": "gate_verdict",
        "value": 1.0 if verdict["passed"] else 0.0,
        "grouping": {"threshold": verdict["threshold"],
                     "adjudication_can_change_verdict": verdict["adjudication_can_change_verdict"]},
    })

    model = extractor_cfg["model"]
    weights = model.get("weights") or {}
    resolved_config = {
        "experiment": GATE_ID,
        "batch": batch.name,
        "n_items": verdict["n_items"], "n_cells": verdict["n_cells"],
        "annotators": list(verdict["annotators"]),
        "n_disputed": verdict["n_disputed"],
        "adjudication": adjudication.name if adjudication else None,
        "adjudication_can_change_verdict": verdict["adjudication_can_change_verdict"],
        "claims_key": claims_key,
        "extractor": {
            "id": extractor_cfg["id"], "version": version,
            "prompt": dict(extractor_cfg["prompt"]),
            "model": {k: model[k] for k in ("model_family", "quantisation", "runtime") if k in model},
            "weights": dict(weights),
        },
        "criterion": "extractor_f1 (amendment 0004: defaults excluded both sides)",
        "threshold": verdict["threshold"],
        "threshold_ref": "statistics:decision_thresholds:extractor_f1",
        "results": {k: dict(v) for k, v in verdict["results"].items()},
        "gate_passed": bool(verdict["passed"]),
    }

    inputs = [_ref(batch / "audit_batch.jsonl", "audit_batch"),
              _ref(batch / "audit_key_DO_NOT_SHOW_ANNOTATOR.json", "audit_key"),
              _ref(batch / "feature_vocabulary.json", "feature_vocabulary")]
    inputs += [_ref(p, "annotation") for p in pass_files]
    if adjudication:
        inputs.append(_ref(adjudication, "adjudication"))
    ledger = batch / "_llm_extraction_cache"
    if ledger.is_dir():
        inputs += [_ref(p, "llm_ledger") for p in sorted(ledger.iterdir()) if p.is_file()]

    identity = weights.get("hf_repo") or extractor_cfg["id"]
    if weights.get("file"):
        identity += f"/{weights['file']}"
    if weights.get("sha256"):
        identity += f"@{weights['sha256'][:12]}"
    return write_run(
        runs_root, run_id=mint_run_id(GATE_ID, code_version, now),
        experiment_id=GATE_ID, artifacts=art, resolved_config=resolved_config,
        code_version=code_version,
        environment={"environment_hash": sha256_json(
            {"gate": "extractor_audit", "extractor_version": version})},
        seeds={"extraction/llm": 0}, inputs=inputs,
        models=[ModelRef("extractor", identity, quantisation=model.get("quantisation"),
                         revision=weights.get("revision"))],
        gate="PASSED" if verdict["passed"] else "FAILED",
    )
