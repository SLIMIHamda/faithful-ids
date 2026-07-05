"""Cheap, local guards that mirror the import-linter contracts.

`lint-imports` is the authoritative gate (CI job `import-contracts`). These tests
are a fast local backstop for the two most load-bearing rules — the pure L0
theory layer (edge 7) and the metrics/generation firewall (edges 1 & 3) — so a
violation is caught by `pytest` even when import-linter is not installed.

They parse the AST statically; no heavy dependency is imported.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "faithfulids"


def _internal_imports(pkg_dir: Path) -> set[str]:
    found: set[str] = set()
    for py in pkg_dir.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("faithfulids."):
                        found.add(a.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.startswith("faithfulids") or node.level:
                    # normalise relative imports to the target package name
                    found.add(mod if mod.startswith("faithfulids") else f"rel:{mod}")
    return found


def test_framework_imports_nothing_internal_but_framework():
    imports = _internal_imports(SRC / "framework")
    offending = {
        m
        for m in imports
        if m.startswith("faithfulids.") and not m.startswith("faithfulids.framework")
    }
    assert offending == set(), f"framework (L0) must stay pure; offending: {offending}"


def test_provenance_does_not_import_higher_layers():
    imports = _internal_imports(SRC / "provenance")
    allowed_prefixes = ("faithfulids.provenance",)
    offending = {
        m
        for m in imports
        if m.startswith("faithfulids.") and not m.startswith(allowed_prefixes)
    }
    assert offending == set(), f"provenance (L0) leaked an import: {offending}"
