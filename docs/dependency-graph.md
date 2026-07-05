# Dependency graph and import contracts

Layers (a layer may import strictly downward; enforced by import-linter in CI,
configured in [`pyproject.toml`](../pyproject.toml) `[tool.importlinter]`):

```
L0  framework, provenance                (pure definitions; import nothing internal)
L1  datasets                             (-> L0)
L2  detectors, attribution, llm          (-> L1, L0)
L3  generation, extraction, corruption   (-> L2, L1, L0)
L4  metrics                              (-> L0 schemas, L2 artifacts; NOT L3 generation)
L5  orchestration, results               (-> everything below)
---- repository boundary ----
A   analysis/                            (-> faithfulids.results + faithfulids.framework ONLY)
P   paper/figures, paper/tables          (-> analysis/outputs files ONLY; no faithfulids imports)
```

## The seven named forbidden edges

Each is a CI contract. Edges 1, 2, 3, 6, 7 and 4 are import-linter contracts;
edge 5 is enforced structurally (notebooks is not a package) plus
`no-notebook-in-pipeline.yml`; the paper boundary (P) is enforced by a grep gate
in `figure-regen.yml`.

| # | Forbidden edge | Enforcement |
|---|---|---|
| 1 | `metrics.* → generation.*` | import-linter `forbidden` |
| 2 | `extraction.* ↔ generation.b4_vte.verifier.*` | import-linter `forbidden` (both directions) + `firewall_check.py` (hashes, families, shared code) |
| 3 | `generation.* → metrics.*` | import-linter `forbidden` |
| 4 | `analysis → orchestration \| generation \| llm` | import-linter `forbidden` (root package `analysis`) |
| 5 | `anything → notebooks/` and `notebooks → runs-writing paths` | `notebooks/` not a package + `no-notebook-in-pipeline.yml` |
| 6 | `detectors` inference paths → training entrypoints | import-linter `forbidden` (`*.predict` may not import `*.train`) |
| 7 | `framework → anything internal` | import-linter `forbidden` (theory layer stays pure) |

No cycles are possible: the graph is a DAG by construction, and the two
firewalled L3 siblings are mutually non-importing.

## Running the check locally

```bash
make import-contracts     # == lint-imports --config pyproject.toml
```

grimp analyses the AST statically, so the heavy scientific stack (torch,
xgboost, shap, transformers) need not be installed to run this gate.

## Why layering alone is insufficient

A layered contract forbids *lower→higher* imports but permits *higher→lower*.
That would allow `metrics` (L4) to import `generation` (L3) — exactly what the
isolation requirement forbids. So the layered contract is paired with explicit
`forbidden` contracts for edges 1 and 3, which the layered rule does not cover.
