# Experiment lifecycle (configuration → published figure)

The path a result travels, illustrated with the Tier A core factorial feeding
the H1 headline (the plausibility–faithfulness gap) and its critical-difference
diagram. This expands blueprint §4.

```
gates ──▶ registration ──▶ execution ──▶ analysis ──▶ figure/table ──▶ mapping ──▶ release
(G-001,   (PR merge =     (make run,     (make        (make figures,  (paper/     (release_
 G-002)    immutable       write-once     analyse H=)   diff hashes)    mapping)    closure)
           registry)       run dir)
```

## Stage 0 — Prerequisites (gates)

- `EXP-G-001` (extractor audit): 300 stratified explanations dual-annotated;
  extractor P/R/F1 vs adjudicated gold + Krippendorff's α; run completes with
  `gate: PASSED`.
- `EXP-G-002` (RQ0 calibration): corruption operators over B1 outputs;
  per-metric ROC/sensitivity/specificity + fluency correlation; passing metric
  set recorded.

Both run IDs become **mandatory references** for Stage 3+. Orchestration refuses
to compute Layer-1 metrics for any run that does not reference a passing gate
run ID.

## Stage 1 — Registration

Author writes `experiments/tier_a/EXP-A-001_core_factorial.yaml` composing
dataset/detector/attribution/LLM/generator/sampling/metric configs **by
reference**, citing the seed-table section, hypothesis family (H1, H2), and gate
dependencies. PR triggers `validate-configs` + `mapping-completeness`. **Merge =
registration.** The registry entry is now immutable.

## Stage 2 — Execution

`make run EXP=EXP-A-001`. Orchestration:

1. resolves + snapshots the config (`config.resolved.yaml`);
2. verifies the environment fingerprint against the lock;
3. verifies gate references are PASSED;
4. refuses a dirty worktree (unless debug mode → `NON-CITABLE`);
5. mints run ID `EXP-A-001__<git-sha>__<utc>`;
6. expands 44 cells;
7. runs stages per cell: *load frozen split → load frozen detector →
   compute/reuse cached attributions → generate explanations (LLM through the
   logging client) → extract claims (firewalled extractor) → compute
   Layer-1/Layer-2/plausibility/cost metrics*;
8. writes artifacts + `MANIFEST.json`; sets `STATUS=COMPLETE`.

Any parameter not in the snapshot cannot influence the run — the runner has no
other inputs.

## Stage 3 — Statistical analysis

`analysis/configs/h1_gap.yaml` enumerates the exact run IDs and references
pre-registered tests + thresholds. `make analyse H=h1_gap` loads artifacts
through the read-only results API (hash-verified), computes, writes a manifested
output directory.

## Stage 4 — Figure/table generation

`paper/figures/specs/fig_cd_diagram.yaml` names its analysis-output directory +
script. `make figures` regenerates `generated/fig_cd_diagram.pdf`; the spec's
expected hash is updated in the same commit; CI re-runs generation and diffs.

## Stage 5 — Paper assembly & traceability

`paper/mapping.yaml` gains the row:
`Figure 4 → fig_cd_diagram → analysis h1_gap__<sha> → runs [EXP-A-001__…] →
experiments [EXP-A-001] → gates [EXP-G-001, EXP-G-002]`.
`mapping-completeness` verifies every cited run exists, is COMPLETE,
non-exploratory, and hash-verifies.

## Stage 6 — Release

`release_closure.py` assembles the Zenodo bundle (code at tag, manifests,
analysis outputs, run artifacts or L3-sufficient caches) and verifies closure.
See [`reproducibility-guide.md`](reproducibility-guide.md) for the tiers.

## Failure path

A failed run keeps its directory and `STATUS=FAILED` forever. The fix is a
code/config change (new commit, possibly a superseding registry entry) and a
**new** run. History is never rewritten.
