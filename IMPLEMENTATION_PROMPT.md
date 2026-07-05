# Implementation Prompt — `beyond-plausibility` Research Repository

> Paste this prompt into a fresh coding session. Attach `REPOSITORY_BLUEPRINT.md` — it is the
> authoritative architecture specification. This prompt is self-contained regarding scientific
> parameters; the PDFs are optional background.

---

## Role

You are the Lead Research Software Engineer implementing the reproducibility infrastructure for a
Q1 journal artifact: *Beyond Plausibility: Measuring and Enforcing Faithfulness in LLM-Generated
Explanations for Intrusion Detection* (target venue: Computers & Security).

You are implementing **infrastructure, not experiments**. No experiment is run, no dataset is
downloaded, no LLM is called, and no scientific result is produced in this engagement. You are
building the machine that will later run them under full provenance.

## Authoritative specification

The attached `REPOSITORY_BLUEPRINT.md` defines the complete architecture: directory tree,
directory contracts, dependency layers, forbidden import edges, provenance model, experiment
lifecycle, CI gates, and the reproducibility audit remediations. **Implement it as written.**
Where this prompt and the blueprint conflict, the blueprint wins. Where the blueprint is silent,
apply the governing dogma:

> Scientific rigor and reproducibility take absolute priority over software convenience.

## Immutable constraints (violating any of these is a failed implementation)

1. **No scientific parameter in code.** No magic constants, no hardcoded paths, no hardcoded model
   names, no defaults for scientific parameters. A missing config key is a hard error. All
   parameters live in `configs/` and are validated against JSON Schemas in `configs/schema/`.
2. **Write-once `runs/`.** The orchestration layer must make mutation of an existing run directory
   impossible through the API (open a new run ID or refuse). Terminal statuses (COMPLETE/FAILED)
   are immutable.
3. **The circularity firewall is structural.** `src/faithfulids/extraction/` and
   `src/faithfulids/generation/b4_vte/verifier/` share no code, no prompts, no model family.
   Enforce with import-linter contracts + a `tools/firewall_check.py` that verifies prompt-hash
   disjointness and config-declared model-family disjointness. Both run in CI.
4. **Layered imports, enforced.** Configure import-linter with the exact layer rules and the seven
   named forbidden edges from blueprint §5. CI fails on violation.
5. **Metrics are generator-blind by type.** Metric function signatures must not accept generator
   identity. Grouping keys are attached downstream by orchestration.
6. **Dirty-worktree runs are refused.** The runner records git commit + dirty flag and aborts on
   dirty (except an explicit debug mode that stamps outputs NON-CITABLE).
7. **Determinism is tested.** Same seed → byte-identical outputs for every CPU stage; a CI job
   runs a toy pipeline twice and diffs.
8. **Nothing silently regenerates.** Caches are content-addressed by the hash of all inputs; a
   changed input creates a new entry.
9. **No `utils/`, `common/`, `helpers/`, `misc/` modules.** Every module maps to a scientific
   responsibility named in the blueprint.
10. **Notebooks are quarantined.** Nothing under `notebooks/` may be imported by pipeline code;
    add the CI check.

## Scientific parameters to encode (in configs, schemas, and stubs — not in code)

- **Anchor configuration:** corrected CICIDS2017 × XGBoost × Llama-3.1-8B-Instruct
  (`experiments/ANCHOR.yaml`, referenced — never restated — by Tier B entries).
- **Tier A core factorial:** datasets {cicids2017_corrected, unsw_nb15} × detectors {xgboost/exact
  TreeSHAP, ft_transformer/DeepSHAP} × LLMs {mistral_7b_instruct, llama31_8b_instruct,
  frontier_api} × generators {B0 raw SHAP, B1 deterministic template, B2 zero-shot, B3 DTE-style,
  B4 Verify-then-Explain}. B0/B1 are LLM-independent (`llm_dependent: false` in generator configs)
  → cell expansion must yield 2 + 3×3 = 11 generator–LLM cells per dataset×detector, 44 total.
- **Tier B anchored extensions (one factor at a time):** transfer to cse_cic_ids2018 (anchor
  pipeline trained on CICIDS2017; B1/B2/B4 only); 4-bit quantisation of Mistral-7B and
  Llama-3.1-8B (B2, B4); Random Forest detector continuity (B1/B2/B4); sensitivity micro-sweeps
  top-k ∈ {3,5,8}, temperature ∈ {0, 0.7}, verifier threshold × 3 levels (B4 only).
- **Sampling:** n = 400 explained instances per dataset, stratified per attack class, minority
  floor 30 (oversample the explanation set, not training); all seeds from
  `configs/seeds/seed_table.yaml`.
- **Stochasticity protocol:** 100-instance subsample per cell, k = 3 generations at operating
  temperature; headline runs at temperature 0.
- **Gate experiments (hard dependencies):**
  - `EXP-G-001` extractor audit: 300 dual-annotated explanations; gate extractor F1 ≥ 0.95;
    report Krippendorff's α. Orchestration must refuse Layer-1 metric computation for any run not
    referencing a passing gate run ID.
  - `EXP-G-002` RQ0 metric calibration: corruption operators over B1 outputs — fabricated
    feature, sign flip, rank inversion, omission, magnitude inflation, vague substitution — with
    ground-truth labels; gate per-metric sensitivity ≥ 0.9 and specificity ≥ 0.9; metrics must be
    weakly correlated with fluency.
- **Layer-1 metrics:** feature-mention precision/recall/F1, Directional Sign Agreement (DSA),
  Attribution Rank Correlation (ARC), Hallucinated-Feature Rate (HFR) — over extracted claim
  tuples (feature, direction, rank, magnitude).
- **Layer-2 metrics:** ERASER-style comprehensiveness & sufficiency at k ∈ {1,3,5}; primary
  erasure operator = conditional-expectation imputation (per-class kNN or light generative model,
  fitted models are manifested cache artifacts); secondary = retrain-based ROAR at the anchor
  only. Erasure background is deliberately NOT the SHAP baseline distribution.
- **Extraction:** rule-assisted LLM extractor, fixed model, frozen prompt, temperature 0; model
  family disjoint from all generator/verifier families (schema-enforced).
- **Plausibility judge:** LLM-as-judge for plausibility ONLY (never faithfulness); judge family
  used by no explainer; validation gate Spearman ρ ≥ 0.6 vs human annotations or the judge is
  dropped; randomized order + length-stratified reporting.
- **Statistics (pre-registered, frozen at git tag `prereg-v1`):** Friedman + Nemenyi with
  critical-difference diagrams; Wilcoxon signed-rank pairs; bootstrap 95% CIs + effect sizes on
  all headline numbers; Holm–Bonferroni within pre-declared families {H0, H1, H2, H3, H-T, H4};
  variance components (instance, generation, extraction) as random effects; decision thresholds:
  H2 ≥ 10-point absolute Layer-1 F1/DSA drop; H-T Cohen's d ≥ 0.4 at ≤ 5-point faithfulness
  deficit. Coverage–risk curves + AURC for B4 abstention; on abstention, fallback degrades to B1
  (never silence).
- **Firewall rules (blueprint §8-A4):** H3 headline evidence only from verifier-independent
  signals; distinct extractor/verifier implementations; abstention reported as coverage–risk;
  verifier threshold tuned on held-out dev split only.
- **Exploratory:** `EXP-X-001` CTI-RAG at the anchor — schema flag `exploratory: true`; CI blocks
  exploratory runs from headline figure/table mappings.

## Deliverables, in phases (each phase ends with green CI before the next begins)

**Phase 0 — Skeleton + governance.** Full directory tree from blueprint §1 (with `.gitkeep` +
per-directory `README.md` stating its contract from blueprint §2); `pyproject.toml`, `uv.lock`,
`Makefile` targets (`run`, `analyse`, `figures`, `paper`, `reproduce-l1`, stubs failing loudly
where unimplemented); `environment/Dockerfile`; all CI workflows from the tree (initially the
ones that can pass: config validation, import contracts, no-notebook, docs build); import-linter
configuration with all layers and forbidden edges; `CITATION.cff`, licenses, `CHANGELOG.md`.

**Phase 1 — Provenance + framework (L0).** `framework/schemas.py` (claim tuple, explanation
record, attribution artifact), `framework/interfaces.py`, `framework/decomposition.py`
(definitions only); `provenance/` manifest writer/verifier implementing the blueprint §6 manifest
schema (`provenance/manifest.v1.json`), content hashing, run-ID minting, dirty-flag refusal.
Unit tests + schema round-trip tests.

**Phase 2 — Config system + registry.** JSON Schemas for every config family in the tree;
reference resolution (configs reference other configs, prompts by hash, KB by version, seeds by
table section) producing a flattened `config.resolved.yaml`; the experiment registry loader;
schema flag handling (`exploratory`, `llm_dependent`); write ALL config files listed in the
blueprint tree with real parameter values from this prompt. Cell-expansion logic with a unit test
asserting exactly 44 Tier A cells.

**Phase 3 — Data + detectors + attribution (L1–L2).** Dataset loader interfaces; the correction
pipeline as versioned, tested transforms (implement structure + checksum verification; actual
Engelen/Lanvin fix rules can be stubbed with TODO-marked, tested placeholders that hard-fail if
executed unimplemented — never silently pass through); split materialisation writing
`split_manifest.json`; detector train/infer separation with frozen artifacts to `models/`;
attribution base interface + TreeSHAP/DeepSHAP wrappers; content-addressed attribution cache.

**Phase 4 — LLM client + generation + extraction + corruption (L3).** Provider-agnostic LLM
client with append-only call ledger, pinned-snapshot enforcement, and cache-only replay mode
(L3 reproduction); prompt registry loader with hash verification; the five generator subpackages
(B0/B1 fully implementable now — B1 is the deterministic template, faithful by construction;
B2/B3/B4 implement structure + prompt wiring); B4 verifier + abstention + KB retrieval as
specified; the firewalled extractor; the six RQ0 corruption operators emitting ground-truth
labels. `tools/firewall_check.py` + CI job.

**Phase 5 — Metrics (L4).** Layer-1, Layer-2 (both erasure operators), meta-validation
(ROC/sens/spec vs corruption ground truth), plausibility-judge harness, cost accounting. Every
metric ships with a hand-computed fixture in `tests/metrics_fixtures/` and a formula version in
its config.

**Phase 6 — Orchestration + results API (L5).** Stage runner (attribution → generation →
extraction → metrics) with per-stage manifests; gate enforcement; STATUS lifecycle;
`faithfulids.results` read-only API with hash verification. End-to-end 5-instance toy pipeline
in `tests/pipeline_smoke/` using a fake deterministic LLM — this powers the determinism CI job.

**Phase 7 — Analysis + paper + tooling.** Statistical pipelines in `analysis/src/`; analysis
configs referencing enumerated run IDs; figure/table spec+script pattern with two working
examples (CD diagram, coverage–risk curve) driven by the toy pipeline's outputs;
`paper/mapping.yaml` format + `mapping-completeness` CI; `tools/audit_manifests.py`,
`tools/lineage_graph.py`, `tools/prereg_diff.py`, `tools/release_closure.py`; all `docs/` files
written (not stubs — the blueprint gives you the content basis); `REPRODUCING.md` with the L1–L4
tiers.

## Definition of done

- All CI jobs green; import-linter contracts active; firewall check passing.
- `make run EXP=EXP-TOY-001` executes the toy experiment twice with identical seeds and produces
  byte-identical metrics; the run directories are complete with valid manifests.
- `tools/lineage_graph.py` renders the full lineage DAG for a toy figure down to prompt hashes
  and seeds.
- A new dataset or generator can be added by writing configs (+ one subpackage for a generator)
  with zero edits to evaluation code — demonstrate with a test.
- No file anywhere contains a hardcoded path, model name, threshold, or seed outside `configs/`.

## Forbidden actions

- Do not fabricate scientific results, example outputs "for illustration," or placeholder metric
  values that could be mistaken for real results.
- Do not download datasets or call any LLM API.
- Do not "simplify for now" in ways that violate the immutable constraints — if a constraint is
  expensive, implement the constraint and stub the science, never the reverse.
- Do not add dependencies without pinning; do not use `try/except ImportError` optional-dependency
  patterns for scientific components.

Work phase by phase. At the end of each phase, summarize what was built, show the CI status, and
list any deviation from the blueprint with its justification before continuing.
