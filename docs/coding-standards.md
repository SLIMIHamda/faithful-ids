# Coding standards

The standards exist to protect reproducibility, not taste. Where a rule below is
inconvenient, the rule wins (governing dogma).

## Hard rules (CI-enforced)

1. **No scientific parameter in code.** No magic constant, path, model name,
   threshold, or seed literal anywhere in `src/`. All come from `configs/`. A
   missing config key raises — never a silent default.
2. **No `utils/` / `common/` / `helpers/` / `misc/` modules.** Every module maps
   to a scientific responsibility named in the blueprint.
3. **Respect the layers.** Import strictly downward; see
   [`dependency-graph.md`](dependency-graph.md). `lint-imports` gates this.
4. **No optional-dependency `try/except ImportError`** for scientific
   components. If a science path needs a dependency, it is a hard, pinned
   dependency; the module imports it at top level. (Lazy import *by config-named
   path* in the orchestration registry is allowed — that is dispatch, not an
   optional fallback.)
5. **No absolute paths, no drive letters** in any config or committed artifact
   (schema regex, hostile-audit A10). Use `pathlib` and repo-relative paths in
   code.
6. **Determinism-critical stages set and record their seeds/flags.** Seeds come
   from the seed table; flags are written into the manifest.

## Style

- Python ≥ 3.11, `from __future__ import annotations`, full type hints; `mypy
  --strict` on `src/faithfulids`.
- `ruff` for lint/format; line length 100.
- Docstrings state the *scientific* responsibility and the invariants a module
  upholds, not just the mechanics.
- Prefer explicit dataclasses/TypedDicts (see `framework/schemas.py`) over loose
  dicts at package boundaries.

## Stubs that must fail loudly

Where the science is not yet implemented (e.g. specific Engelen/Lanvin fix
rules), the placeholder **raises** `NotImplementedError` with a `TODO` marker and
is covered by a test asserting it raises. It must never silently pass data
through — a silent pass-through is a fabricated result waiting to happen.

## Forbidden

Fabricating results, example outputs "for illustration", or placeholder metric
values that could be mistaken for real results. See
[`contributing.md`](contributing.md).
