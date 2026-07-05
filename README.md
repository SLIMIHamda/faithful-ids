# Beyond Plausibility — reproducibility artifact

Infrastructure for the paper *Beyond Plausibility: Measuring and Enforcing
Faithfulness in LLM-Generated Explanations for Intrusion Detection*
(target venue: **Computers & Security**).

> **Governing dogma.** Scientific rigor and reproducibility take absolute
> priority over software convenience. Every architectural decision in this
> repository is justified against that dogma — see
> [`docs/architecture.md`](docs/architecture.md).

This repository is the **machine that runs the experiments under full
provenance**, not the experiments themselves. Cloning it downloads no dataset,
calls no LLM, and produces no scientific result until you register and run an
experiment.

## What the paper claims (and where the evidence lives)

The paper argues that fluency/plausibility of an LLM-generated IDS explanation
is **not** faithfulness, introduces a two-layer faithfulness measurement
(Layer-1 claim-level, Layer-2 erasure-based), meta-validates those metrics
against known corruptions (RQ0), and enforces a *circularity firewall* so that
the Verify-then-Explain generator is never graded by its own verifier. Every
headline number traces — mechanically — through
`paper/mapping.yaml → analysis/outputs → runs/ → experiments/ → configs/ + prompts/ + seeds/ + commit`.

## Three-command quickstart (per reproduction tier)

Reproduction tiers are defined in [`REPRODUCING.md`](REPRODUCING.md). Every
command goes through the `Makefile` — the **only** sanctioned entry points.

```bash
# L1 — regenerate every figure & table from released analysis outputs (CPU, <30 min)
make reproduce-l1

# L2 — recompute every statistic from released run artifacts
make analyse H=h1_gap

# toy end-to-end (no dataset, no GPU, no API) — powers the determinism CI gate
make run EXP=EXP-TOY-001
```

## Repository map (paper-shaped)

```
framework → datasets/detectors/attribution → generation → extraction/corruption
          → metrics → experiments → analysis → paper → artifact
```

Read it with the paper's table of contents in hand. There is deliberately no
`utils/`, `common/`, or `helpers/` — every module maps to a scientific
responsibility. Full contract per directory: [`docs/architecture.md`](docs/architecture.md)
and the `README.md` in each directory.

## Load-bearing invariants (enforced in CI, not by discipline)

1. **All scientific parameters live in `configs/`.** Source code has no magic
   constants, hardcoded paths, model names, thresholds, or seeds. A missing
   config key is a hard error.
2. **`runs/` is write-once.** Re-execution mints a new run ID; terminal statuses
   are immutable.
3. **The circularity firewall is structural** — separate packages, disjoint
   prompt trees (hash-checked), schema-enforced model-family disjointness,
   import-linter contracts, and `tools/firewall_check.py`.
4. **Metrics are generator-blind by type** — a metric function cannot receive
   "which generator wrote this".
5. **Dirty-worktree runs are refused** (except an explicit debug mode that
   stamps outputs `NON-CITABLE`).
6. **Determinism is tested** — same seed ⇒ byte-identical CPU-stage outputs.
7. **Nothing silently regenerates** — caches are content-addressed.
8. **Notebooks are quarantined** — nothing under `notebooks/` may be imported by
   pipeline code.

## Status

Built phase by phase per [`IMPLEMENTATION_PROMPT.md`](IMPLEMENTATION_PROMPT.md).
See [`CHANGELOG.md`](CHANGELOG.md) for what each phase delivered. This is
infrastructure: **no experiment has been run.**

## License

Code: MIT (`LICENSE`). Prompts, KB, annotations, and generated data carry their
own terms (`LICENSE-ARTIFACTS.md`). Datasets are **not** redistributed.
