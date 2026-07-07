# Changelog

Versioned artifact history. `v1.0` = submission, `v1.1` = camera-ready, etc.
Metric *formula versions* and superseding registry entries are recorded here so
that a corrected metric or a re-run experiment leaves a public trail rather than
silently replacing history (see hostile-audit remediation A12 in
`docs/architecture.md`).

The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project adheres to [Semantic Versioning](https://semver.org/) for the artifact.

## [Unreleased]

### Infrastructure (no scientific results produced)

This artifact is being built phase by phase per `IMPLEMENTATION_PROMPT.md`.
No experiment has been run, no dataset downloaded, no LLM called.

- **Phase 0** — Repository skeleton and governance: full directory tree with
  per-directory contracts, packaging (`pyproject.toml`), `Makefile` entry
  points, container definitions, CI workflow set, import-linter layered
  contracts + the seven named forbidden edges, licenses, citation metadata.
- **Phase 1** — L0 `framework` (claim/explanation/attribution schemas,
  generator-blind metric interfaces, ε_model ≲ ε_nar + ε_att decomposition) and
  `provenance` (content hashing, run-ID minting, dirty-worktree refusal, §6
  manifest writer/verifier, immutable STATUS lifecycle).
- **Phase 2** — Config system: JSON Schemas for every family, all config /
  experiment / KB files with real parameters, prompt registry with hash
  verification, reference resolution, and cell expansion proven to yield exactly
  44 Tier A cells.
- **Phase 3** — L1 dataset loaders + Engelen/Lanvin correction pipeline
  (hard-fail stubs) + split materialisation; L2 detector train/infer artifact
  boundary + attribution base + content-addressed cache.
- **Phase 4** — L2 provider-agnostic LLM client (append-only ledger,
  pinned-snapshot enforcement, cache-only replay); L3 generators (B0/B1 faithful
  & deterministic, B2–B4 wired, B4 abstains to B1), firewalled extractor, six
  RQ0 corruption operators, and `tools/firewall_check.py`.
- **Phase 5** — L4 metrics (Layer-1, Layer-2 erasure incl. conditional-
  expectation imputation + structured ROAR, RQ0 meta-validation, plausibility
  judge, cost) — generator-blind, each with a hand-computed fixture.
- **Phase 6** — L5 stage runner with per-stage manifests, gate enforcement,
  read-only results API, and the deterministic 5-instance toy pipeline that
  powers the determinism gate.
- **Phase 7** — Analysis statistics (Friedman+Nemenyi, Wilcoxon+Holm, bootstrap
  CIs, coverage–risk/AURC, variance components, mixed effects), the analysis
  runner, the figure/table spec→script→generated pattern (CD diagram,
  coverage–risk curve, Layer-1 summary table) driven by the toy outputs,
  `paper/mapping.yaml`, and the four self-audit tools (`audit_manifests`,
  `lineage_graph`, `prereg_diff`, `release_closure`).

### Pilot-v1 post-mortem — Pass A (instrument repair, pre-freeze)

The first real pilot (`EXP-PILOT-001__371f2d8`) completed but exposed a Layer-2
instrument fault. See `docs/adr/0001-layer2-eps-model-claim-driven.md`.

- **Layer-2 now measures ε_model (claim-driven).** Added `comprehensiveness_cited`
  / `sufficiency_cited`, which erase the top-k **cited** features (S from the
  `ClaimSet`) per (instance, generator). The prior attribution-driven metrics are
  kept and relabeled **ε_att** (claim-free, generator-blind). Metric rows carry a
  `component` field. The generator-blindness firewall is preserved: metrics receive
  claim *content*, never generator *identity* (import Edge 1 still KEPT).
- **Saturation-safe deltas.** Layer-2 metrics gained `delta_space` ∈
  {`prob` (default), `margin`}; `DetectorArtifact.predict_margin` added (XGBoost
  `output_margin=True`, logit fallback). Emitted runs remain `prob` pending the
  saturation diagnostic.
- **Erasure-efficacy CI smoke test** added (erase-all ⇒ material Δ; erase-none ⇒ 0).
- **Imbalance-aware detector competence gate.** A run is refused before any tokens
  unless the detector clears macro-F1 AND a per-attack-family detection-recall
  floor on the held-out explanation set; the full per-family table → `competence.json`
  + the run manifest, with a logged exemption list in the detector config.
- **Generation revisions pinned.** All open-weights LLM configs pinned to explicit
  HF commit hashes; `configs/schema/llm.v1.json` rejects any `weights.revision` that
  is not a 40-char commit, making an unpinned generation revision structurally
  impossible. Pilot-v1's own revision is unrecoverable (it ran unpinned).
- **Saturation diagnostic** (`tools/layer2_saturation_diagnostic.py` + the tested
  `metrics.layer2.saturation` core) recomputes both Layer-2 families in prob and
  margin space over a run's re-derived inputs — read-only, no new tokens.

### Metric formula versions / schema

- `configs/metrics/layer2_erasure.yaml`: `1.0.0 → 1.1.0` (additive — new ε_model
  family; ε_att metrics unchanged).
- Schema (backward-compatible): `metric.v1.json` gains optional `component` /
  `delta_space`; `detector.v1.json` gains optional `competence_gate`;
  `llm.v1.json` requires `weights.revision` to be a 40-char commit hash (enforced
  going forward; satisfied by the now-pinned configs).

All 105 unit/contract/smoke/determinism tests pass; import-linter (8 contracts),
firewall-audit, validate-configs, data-integrity, manifest-audit,
mapping-completeness, release-closure, prereg-freeze, and doc-links are green.

<!--
Template for future entries:

## [1.0.0] - YYYY-MM-DD  (submission)
### Added
### Changed
### Metric formula versions
### Superseding registry entries
-->
