# Architecture

This document is the maintained companion to
[`REPOSITORY_BLUEPRINT.md`](../REPOSITORY_BLUEPRINT.md), which is the
authoritative specification. Read the blueprint for the full directory tree and
per-directory contracts; read this for the standing summary and the pointers a
maintainer needs.

> **Governing dogma.** Scientific rigor and reproducibility take absolute
> priority over software convenience.

## The five load-bearing commitments

1. **The experiment registry is append-only and configuration-complete.** An
   experiment exists iff it has a registered, schema-validated YAML in
   [`experiments/`](../experiments). Amendments create a new versioned entry
   that supersedes; they never edit a run entry.
2. **`runs/` is a write-once ledger.** Every run writes an ID-addressed
   directory with a resolved-config snapshot and a cryptographic manifest.
   Re-execution creates a new run directory.
3. **The circularity firewall is enforced by structure.** See
   [`firewall.md`](firewall.md).
4. **Statistics and figures are pure consumers.** `analysis/` reads `runs/**`
   through a read-only API; `paper/` reads only `analysis/outputs/**`.
5. **Pre-registration is a git event.** Hypotheses, thresholds, and the
   human-study plan are tagged `prereg-v1` before Tier A runs; CI freezes them.

## Layering

The library ([`src/faithfulids/`](../src/faithfulids)) is layered L0–L5 and a
layer imports strictly downward. The rules and the import-linter contract
listing are in [`dependency-graph.md`](dependency-graph.md).

## Provenance model

Every artifact directory carries a `MANIFEST.json` conforming to
`provenance/manifest.v1.json`. Lineage closure lets `tools/lineage_graph.py`
reconstruct the full DAG behind any paper asset. See [`lineage.md`](lineage.md).

## Hostile reproducibility audit (self-review)

The blueprint §8 answers twelve standard rejection vectors (A1–A12) with a
mechanical control rather than a promise. The mapping of each remediation to its
enforcing mechanism:

| # | Attack | Enforcing mechanism |
|---|---|---|
| A1 | Frontier API model disappears | append-only LLM ledger + L3 replay CI |
| A2 | Temperature 0 ≠ determinism | stochasticity protocol + recorded torch flags + tolerance policy |
| A3 | Datasets not redistributable | deterministic correction pipeline + `data-integrity.yml` |
| A4 | Firewall is a promise | separate packages + `firewall-audit.yml` + import contracts |
| A5 | Prereg back-dated | OSF DOI external timestamp + `prereg-freeze.yml` |
| A6 | `runs/` immutability is convention | manifests+hashes in git + `manifest-audit.yml` |
| A7 | Run selection = p-hacking | enumerated run IDs + `mapping-completeness.yml` |
| A8 | Human-study not reproducible | prereg code + `synthetic_sample/` + instruments released |
| A9 | Author-annotated audit set | separate pools + released adjudication log |
| A10 | Windows→Linux drift | container digest in manifest + no absolute paths (schema) |
| A11 | Fitted erasure models hidden | imputation models are manifested cache artifacts |
| A12 | Metric bug after Tier A | formula versions + superseding entries + CHANGELOG |

## Where things live

| Concern | Location |
|---|---|
| Parameters | [`configs/`](../configs) |
| Prompts (instruments) | [`prompts/`](../prompts) |
| KB (VtE grounding) | [`kb/`](../kb) |
| Library | [`src/faithfulids/`](../src/faithfulids) |
| Registry | [`experiments/`](../experiments) |
| Ledger | [`runs/`](../runs) |
| Statistics | [`analysis/`](../analysis) |
| Paper assets | [`paper/`](../paper) |
| Self-audit tools | [`tools/`](../tools) |
