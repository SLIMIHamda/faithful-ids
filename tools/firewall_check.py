#!/usr/bin/env python3
"""The circularity firewall as a mechanical gate (CI job `firewall-audit`).

Verifies that the VtE internal verifier (side A) and the evaluation extractor
(side B) share no ground:

1. **prompt-hash disjointness** — no sha256 collision between the verifier prompt
   tree and the extractor prompt tree;
2. **wording disjointness** — no identical non-trivial prompt line across the two
   trees (a copy with trivial edits is caught by the hash check);
3. **model-family disjointness** — the verifier family, the extractor family, and
   every generator LLM family are pairwise disjoint, and the plausibility judge
   family is disjoint from all explainer families;
4. **import disjointness** — no module under ``extraction/`` imports
   ``generation.*`` and no module under ``generation/b4_vte/verifier/`` imports
   ``extraction.*``.

Pure standard library + PyYAML. Run: ``python tools/firewall_check.py``.
"""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "faithfulids"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _prompt_files(directory: Path) -> list[Path]:
    """Frozen prompt files only — never the per-directory README.md contracts."""
    return [p for p in directory.rglob("*.md") if p.name.lower() != "readme.md"]


def _normalized_lines(paths: list[Path]) -> set[str]:
    lines: set[str] = set()
    for p in paths:
        for raw in p.read_text(encoding="utf-8").splitlines():
            s = raw.strip().lower()
            if not s or s.startswith("<!--") or "-->" in s or s.startswith("{{"):
                continue
            if len(s) > 30:
                lines.add(" ".join(s.split()))
    return lines


def check_prompt_hash_disjointness(errors: list[str]) -> None:
    verifier = _prompt_files(REPO / "prompts" / "generation" / "b4_vte" / "verifier")
    extractor = _prompt_files(REPO / "prompts" / "extraction")
    vh = {_sha256(p) for p in verifier}
    eh = {_sha256(p) for p in extractor}
    if vh & eh:
        errors.append("firewall: prompt-hash collision between verifier and extractor trees")


def check_wording_disjointness(errors: list[str]) -> None:
    verifier = _prompt_files(REPO / "prompts" / "generation" / "b4_vte" / "verifier")
    extractor = _prompt_files(REPO / "prompts" / "extraction")
    shared = _normalized_lines(verifier) & _normalized_lines(extractor)
    if shared:
        errors.append(
            f"firewall: verifier/extractor prompts share {len(shared)} non-trivial line(s): "
            f"{sorted(shared)[:1]}"
        )


def check_model_family_disjointness(errors: list[str]) -> None:
    b4 = _load(REPO / "configs" / "generators" / "b4_vte.yaml")
    verifier_family = b4["verifier"]["model_family"]
    extractor_family = _load(REPO / "configs" / "extraction" / "eval_extractor.yaml")["model"]["model_family"]
    gen_families = {
        _load(p)["model_family"] for p in (REPO / "configs" / "llms").glob("*.yaml")
    }
    judge_family = _load(REPO / "configs" / "metrics" / "plausibility_judge.yaml")["judge"]["model_family"]

    if verifier_family == extractor_family:
        errors.append(f"firewall: verifier and extractor share model_family {verifier_family!r}")
    if verifier_family in gen_families:
        errors.append(f"firewall: verifier family {verifier_family!r} overlaps a generator LLM family")
    if extractor_family in gen_families:
        errors.append(f"firewall: extractor family {extractor_family!r} overlaps a generator LLM family")
    explainer_families = gen_families | {verifier_family, extractor_family}
    if judge_family in explainer_families:
        errors.append(f"firewall: judge family {judge_family!r} overlaps an explainer family")


def _imports(pkg_dir: Path) -> dict[Path, set[str]]:
    out: dict[Path, set[str]] = {}
    for py in pkg_dir.rglob("*.py"):
        mods: set[str] = set()
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module)
            elif isinstance(node, ast.Import):
                mods.update(a.name for a in node.names)
        out[py] = mods
    return out


def check_import_disjointness(errors: list[str]) -> None:
    for py, mods in _imports(SRC / "extraction").items():
        if any(m.startswith("faithfulids.generation") for m in mods):
            errors.append(f"firewall: {py.relative_to(REPO)} imports generation.*")
    for py, mods in _imports(SRC / "generation" / "b4_vte" / "verifier").items():
        if any(m.startswith("faithfulids.extraction") for m in mods):
            errors.append(f"firewall: {py.relative_to(REPO)} imports extraction.*")


def run() -> list[str]:
    errors: list[str] = []
    check_prompt_hash_disjointness(errors)
    check_wording_disjointness(errors)
    check_model_family_disjointness(errors)
    check_import_disjointness(errors)
    return errors


def main() -> int:
    errors = run()
    if errors:
        print("firewall-audit: FAILED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("firewall-audit: OK — prompt-hash, wording, model-family, and import disjointness hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
