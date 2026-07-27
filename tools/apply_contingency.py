#!/usr/bin/env python3
"""Materialise a class-handling contingency Decision as the bumped taxonomy.

Prereg amendment 0001 registers the ladder and says the resolver's Decision is
applied by **materialising it as the taxonomy config**, "so the drift guard, not
discipline, enforces propagation". This is that step. Nothing else in the
pipeline reads a Decision: the next detector is fitted from
``configs/taxonomy/<dataset>.yaml``, so until the Decision lands there, a
resolved gate failure has changed nothing.

What it does, in order:

1. Reads the competence table a run recorded (``competence.json``) together with
   the Decision that run stamped on it.
2. **Re-resolves the Decision from scratch** against the current taxonomy and the
   frozen thresholds, and refuses to proceed unless it reproduces the recorded
   one. The tool does not trust the record — if the recorded and reproduced
   decisions disagree, something (taxonomy, thresholds, resolver) moved between
   the run and now, and that must be looked at rather than written to disk.
3. Applies it (``contingency.apply_to_taxonomy`` — pure), validates the result
   against the taxonomy schema **and** the merge-map structural rules that
   ``validate-configs`` enforces, and only then writes.

The emitted file keeps the taxonomy's explanatory prose — the lineage argument
for the merge map is scientifically load-bearing and a YAML round-trip would
silently drop it — and gains a provenance header recording which run's gate
produced the change.

Applying a Decision is a **gate between smoke and primary**: the new vocabulary
requires its own detector fit, competence re-evaluation and SHAP re-attribution
before any generation. Existing artifacts are never relabelled.

Run::

    python tools/apply_contingency.py --competence <path/to/competence.json> [--check]
    python tools/apply_contingency.py --run <path/to/run_dir> --new-version 2.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from faithfulids.detectors.contingency import (  # noqa: E402
    RUNG_BINARY,
    Decision,
    apply_to_taxonomy,
)
from faithfulids.detectors.contingency import resolve as resolve_contingency  # noqa: E402
from faithfulids.orchestration.references import resolve_reference  # noqa: E402
from faithfulids.orchestration.validate_configs import _parent_map_errors  # noqa: E402

TAXONOMY_DIR = REPO / "configs" / "taxonomy"
SCHEMA = REPO / "configs" / "schema" / "taxonomy.v1.json"


def _thresholds() -> dict[str, float]:
    """The frozen prereg constants the ladder reads (never hard-coded here)."""
    ref = resolve_reference
    return {
        "recall_floor": float(ref("statistics:decision_thresholds:detector_recall_floor")["value"]),
        "min_support": int(ref("statistics:decision_thresholds:detector_class_min_support")["value"]),
        "macro_f1_min": float(ref("statistics:decision_thresholds:detector_macro_f1_min")["value"]),
        "class_failure_fraction": float(
            ref("statistics:decision_thresholds:contingency_class_failure_fraction")["value"]
        ),
        "min_attack_classes": int(
            ref("statistics:decision_thresholds:contingency_min_attack_classes")["value"]
        ),
    }


def _find_competence(run_dir: Path) -> Path:
    hits = sorted(run_dir.rglob("competence.json"))
    if not hits:
        raise SystemExit(f"no competence.json under {run_dir}")
    if len(hits) > 1:
        raise SystemExit(
            f"{len(hits)} competence.json files under {run_dir}; pass --competence explicitly:\n  "
            + "\n  ".join(str(h) for h in hits)
        )
    return hits[0]


def _bump_major(version: str) -> str:
    """Default bump is MAJOR: removing or merging a canonical class is not
    backward compatible — every existing run's ``target_class`` means something
    different afterwards, so the version must not suggest a drop-in change."""
    major = version.split(".")[0]
    return f"{int(major) + 1}.0.0"


def _validate(new_tax: dict) -> list[str]:
    errors: list[str] = []
    try:
        import jsonschema

        jsonschema.validate(new_tax, json.loads(SCHEMA.read_text(encoding="utf-8")))
    except ImportError:
        errors.append("NOTE: jsonschema not installed — schema check skipped")
    except Exception as exc:  # jsonschema.ValidationError
        errors.append(f"schema: {exc}")
    errors.extend(
        _parent_map_errors(new_tax, set(new_tax["canonical_classes"]), "taxonomy(new)")
    )
    canon = set(new_tax["canonical_classes"])
    for raw, target in new_tax["label_map"].items():
        if target != "excluded" and target not in canon:
            errors.append(f"label_map[{raw!r}] -> {target!r} is not canonical or 'excluded'")
    for cls in new_tax["canonical_classes"]:
        if cls not in set(new_tax["label_map"].values()):
            errors.append(f"canonical class {cls!r} has no raw label mapped to it (orphan)")
    return [e for e in errors if not e.startswith("NOTE:")], [
        e for e in errors if e.startswith("NOTE:")
    ]


def _render(new_tax: dict, old_tax: dict, decision: Decision, source: str) -> str:
    """Emit the taxonomy YAML, preserving the file's prose.

    Hand-rendered rather than ``yaml.safe_dump``ed: the header comments carry the
    lineage argument for the merge map (why FTP+SSH may merge and DoS+DDoS may
    not), which is the part a reviewer will actually interrogate. A dump would
    drop every one of them.
    """
    head = TAXONOMY_DIR / f"{old_tax['id']}.yaml"
    original = head.read_text(encoding="utf-8").splitlines()

    def block(start_key: str) -> list[str]:
        """The comment lines immediately preceding ``start_key:`` in the original."""
        out: list[str] = []
        for i, line in enumerate(original):
            if line.startswith(f"{start_key}:"):
                j = i - 1
                while j >= 0 and original[j].lstrip().startswith("#"):
                    out.insert(0, original[j])
                    j -= 1
                break
        return out

    merged = sorted(decision.merges)
    lines = [
        f"id: {new_tax['id']}",
        f"schema_version: {new_tax['schema_version']}",
        f"kind: {new_tax['kind']}",
        f"dataset: {new_tax['dataset']}",
        f"version: {new_tax['version']}",
        "# APPLIED CONTINGENCY (prereg amendment 0001,",
        "# configs/statistics/amendments/0001-multiclass-class-handling-contingency.md).",
        f"# Superseded v{old_tax['version']}. Materialised by tools/apply_contingency.py from",
        f"# {source}",
        f"#   rung {decision.rung} ({decision.rung_name})",
        f"#   failed the competence gate: {', '.join(decision.failing) or '(none)'}",
        f"#   excluded: {', '.join(decision.exclusions) or '(none)'}",
        f"#   merged:   {', '.join(f'{c} -> {decision.merges[c]}' for c in merged) or '(none)'}",
        "# The verdict came from the held-out COMPETENCE split, never the explained",
        "# set. This vocabulary requires its own detector fit, competence",
        "# re-evaluation and SHAP re-attribution before generation; no existing",
        "# artifact is relabelled to it.",
    ]
    for chunk in _wrap(decision.rationale):
        lines.append(f"#   {chunk}")

    lines += block("canonical_classes")
    lines.append(
        "canonical_classes: [" + ", ".join(new_tax["canonical_classes"]) + "]"
    )
    lines += block("label_map")
    lines.append("label_map:")
    for raw, target in new_tax["label_map"].items():
        key = f'"{raw}"' if ":" in raw or raw != raw.strip() else raw
        lines.append(f"  {key}: {target}")
    lines += block("parents")
    lines.append("parents:")
    for cls, parent in new_tax["parents"].items():
        lines.append(f"  {cls}: {parent}")
    return "\n".join(lines) + "\n"


def _wrap(text: str, width: int = 74) -> list[str]:
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--competence", type=Path, help="path to a run's competence.json")
    src.add_argument("--run", type=Path, help="a run directory (competence.json is located under it)")
    p.add_argument("--dataset", default="cicids2017", help="taxonomy id (default: cicids2017)")
    p.add_argument("--new-version", help="version for the emitted taxonomy (default: major bump)")
    p.add_argument("--check", action="store_true",
                   help="print the decision and the resulting diff; write nothing")
    args = p.parse_args(argv)

    comp_path = args.competence if args.competence else _find_competence(args.run)
    comp_table = json.loads(comp_path.read_text(encoding="utf-8"))
    recorded = comp_table.get("contingency")
    if recorded is None:
        print(
            f"{comp_path}: no 'contingency' record — this is a BINARY run's competence "
            "table (the ladder is defined over canonical classes, not raw labels). "
            "Nothing to apply.",
            file=sys.stderr,
        )
        return 2

    tax_path = TAXONOMY_DIR / f"{args.dataset}.yaml"
    taxonomy = yaml.safe_load(tax_path.read_text(encoding="utf-8"))
    recorded_decision = Decision.from_record(recorded)

    # Reproduce the decision independently — the record is evidence, not authority.
    stats = recorded.get("trigger_stats") or {}
    vocabulary = tuple(stats.get("vocabulary") or recorded_decision.vocabulary)
    reproduced = resolve_contingency(
        comp_table, taxonomy, _thresholds(),
        current_rung=int(stats.get("evaluated_at_rung", 1)),
        vocabulary=vocabulary,
    )
    if reproduced.as_record() != recorded_decision.as_record():
        print("REFUSING: the recorded decision does not reproduce against the current "
              "taxonomy + frozen thresholds.", file=sys.stderr)
        print(f"  recorded:   rung {recorded_decision.rung}, exclusions "
              f"{list(recorded_decision.exclusions)}, merges {dict(recorded_decision.merges)}",
              file=sys.stderr)
        print(f"  reproduced: rung {reproduced.rung}, exclusions {list(reproduced.exclusions)}, "
              f"merges {dict(reproduced.merges)}", file=sys.stderr)
        print("  Something moved between the run and now (taxonomy version, a frozen "
              "threshold, or the resolver). Investigate — do not overwrite.", file=sys.stderr)
        return 1

    print(f"decision reproduced from {comp_path}")
    print(f"  rung {reproduced.rung} ({reproduced.rung_name}), changed={reproduced.changed}")
    print(f"  {reproduced.rationale}")
    absent = stats.get("absent_from_fit") or []
    if absent:
        print(f"  WARNING: {absent} were absent from the fitted vocabulary — the decision "
              f"certifies nothing about them, yet they survive into the new taxonomy.")

    if not reproduced.changed:
        print("nothing to apply: the registered vocabulary stands.")
        return 0
    if reproduced.rung == RUNG_BINARY:
        print("rung 4 (terminal binary) is a NEGATIVE FINDING for the multi-class design, "
              "reported in the main text — not a taxonomy to fit. Nothing written.",
              file=sys.stderr)
        return 3

    new_version = args.new_version or _bump_major(str(taxonomy["version"]))
    new_tax = apply_to_taxonomy(taxonomy, reproduced, new_version=new_version)
    errors, notes = _validate(new_tax)
    for n in notes:
        print(f"  {n}")
    if errors:
        print("REFUSING: the resulting taxonomy is invalid:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    old, new = taxonomy["canonical_classes"], new_tax["canonical_classes"]
    print(f"\ntaxonomy {taxonomy['version']} -> {new_version}")
    print(f"  classes {len(old)} -> {len(new)}: {old}")
    print(f"                          {new}")
    for cls in [c for c in old if c not in new]:
        print(f"  - {cls}")
    for cls in [c for c in new if c not in old]:
        print(f"  + {cls}")

    if args.check:
        print("\n--check: nothing written.")
        return 0

    tax_path.write_text(_render(new_tax, taxonomy, reproduced, str(comp_path)), encoding="utf-8")
    print(f"\nwrote {tax_path}")
    print("NEXT: the new vocabulary needs its own detector fit, competence re-evaluation "
          "and SHAP re-attribution before any generation. Re-run validate-configs, and "
          "record the change in CHANGELOG.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
