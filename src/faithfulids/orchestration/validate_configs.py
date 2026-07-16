"""`validate-configs` CI entrypoint (L5).

Validates every config / experiment / KB file against its JSON Schema, then
cross-validates references: config-to-config refs resolve, prompt hashes match
the registry AND the files on disk, KB versions match, seed sections exist, and
experiment axes/gates point at real entries. A single failure exits non-zero.

Run: ``python -m faithfulids.orchestration.validate_configs``
Needs only ``pyyaml`` + ``jsonschema``.
"""

from __future__ import annotations

import re
import sys

from faithfulids.orchestration.config_loader import (
    ConfigError,
    iter_config_files,
    load_config,
    repo_root,
    validate_file,
)

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _norm_label(s: str) -> str:
    """Normalise a class label for taxonomy lookup — MUST match
    ``faithfulids.datasets.loaders.cicids2017._norm`` (kept in sync by
    ``test_taxonomy_single_source``; the loader can't be imported here — it pulls
    in pandas, and validate-configs runs on pyyaml+jsonschema only)."""
    return _NON_ALNUM.sub(" ", str(s).lower()).strip()
from faithfulids.orchestration.references import (
    _kb_versions,
    collect_prompt_refs,
    resolve_reference,
    verify_prompt,
)
from faithfulids.orchestration.registry import load_all_experiments


def _check_references(config: dict, errors: list[str], where: str) -> None:
    kind = config.get("kind")
    try:
        for pr in collect_prompt_refs(config):
            verify_prompt(pr)
        if kind == "dataset":
            resolve_reference(config["split"]["seed_ref"])
            if config.get("kb_ref"):
                resolve_reference(config["kb_ref"])
        elif kind == "detector":
            resolve_reference(config["attribution_ref"])
        elif kind == "generator":
            if config.get("kb_ref"):
                resolve_reference(config["kb_ref"])
            if config.get("verifier"):
                resolve_reference(config["verifier"]["threshold_ref"])
            if config.get("abstention"):
                resolve_reference(f"generators:{config['abstention']['fallback_generator']}")
        elif kind == "sampling":
            resolve_reference(config["seed_ref"])
        elif kind == "extraction":
            index = load_all_experiments()
            if config["audit_gate_ref"] not in index:
                errors.append(f"{where}: audit_gate_ref {config['audit_gate_ref']} not registered")
        elif kind == "class_taxonomy":
            # every label_map target is a canonical class or the "excluded" sentinel
            canon = set(config["canonical_classes"])
            mapped = set(config["label_map"].values())
            for k, v in config["label_map"].items():
                if v != "excluded" and v not in canon:
                    errors.append(
                        f"{where}: label_map[{k!r}] -> {v!r} is not a canonical class or 'excluded'"
                    )
            # ORPHAN GUARD: a canonical class no raw label maps to would be a dead
            # num_class slot the detector can never predict (and an empty row in every
            # per-class metric).
            for cls in config["canonical_classes"]:
                if cls not in mapped:
                    errors.append(
                        f"{where}: canonical class {cls!r} has no raw label mapped to it "
                        f"(orphan class — map a label or drop the class)"
                    )
        elif kind in ("kb_feature_dictionary", "kb_attack_classes"):
            names = _kb_versions()
            ds, ver = config["dataset"], config["version"]
            if names.get(ds) != ver:
                errors.append(f"{where}: KB {ds} version {ver} != registry {names.get(ds)}")
            if kind == "kb_attack_classes":
                # SILENT-DRIFT GUARD (queue #5.1b): every attack-class KB entry must
                # map to exactly one canonical class (or "excluded") in the single
                # taxonomy config — else the KB's class semantics and the detector's
                # target labels can diverge, invalidating per-class metrics.
                tax = load_config("taxonomy", ds)
                lm = {_norm_label(k): v for k, v in tax["label_map"].items()}
                for entry in config["entries"]:
                    if _norm_label(entry["name"]) not in lm:
                        errors.append(
                            f"{where}: attack class {entry['name']!r} has no mapping in "
                            f"taxonomy:{ds} (silent-drift guard — add it to the taxonomy label_map)"
                        )
    except ConfigError as exc:
        errors.append(f"{where}: {exc}")


def _check_experiment_refs(exp: dict, errors: list[str], where: str) -> None:
    index = load_all_experiments()
    try:
        design = exp["design"]
        if design["mode"] == "factorial":
            axes = design["axes"]
            for d in axes["datasets"]:
                resolve_reference(f"datasets:{d}")
            for d in axes["detectors"]:
                resolve_reference(f"detectors:{d}")
            for m in axes["llms"]:
                resolve_reference(f"llms:{m}")
            for g in axes["generators"]:
                resolve_reference(f"generators:{g}")
        if design.get("anchor_ref") and design["anchor_ref"] not in index:
            errors.append(f"{where}: anchor_ref {design['anchor_ref']} not registered")
        for ref in exp.get("sampling_refs", []):
            resolve_reference(ref)
        for ref in exp.get("metric_refs", []):
            resolve_reference(ref)
        if exp.get("seed_ref"):
            resolve_reference(exp["seed_ref"])
        for gate in exp.get("gate_dependencies", []):
            if gate not in index:
                errors.append(f"{where}: gate_dependency {gate} not registered")
    except ConfigError as exc:
        errors.append(f"{where}: {exc}")


def validate_all() -> list[str]:
    """Validate everything; return a list of human-readable errors (empty = OK)."""
    errors: list[str] = []
    root = repo_root()
    for path in iter_config_files():
        rel = path.relative_to(root)
        try:
            config = validate_file(path)
        except ConfigError as exc:
            errors.append(str(exc))
            continue
        _check_references(config, errors, str(rel))
        if config.get("kind") == "experiment":
            _check_experiment_refs(config, errors, str(rel))
    return errors


def main() -> int:
    errors = validate_all()
    n_files = sum(1 for _ in iter_config_files())
    if errors:
        print(f"validate-configs: {len(errors)} problem(s) across {n_files} files:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"validate-configs: OK — {n_files} config/experiment/KB files valid, all references resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
