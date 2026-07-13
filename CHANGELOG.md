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
  `output_margin=True`, logit fallback). Pilot runs emit Layer-2 in **both** spaces
  (config `delta_spaces: [prob, margin]`), so a single run answers the saturation
  question; the toy pipeline stays prob-only (determinism unaffected).
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
- **Pilot-v2 launcher.** Generator LLM is selectable per run
  (`FAITHFULIDS_PILOT_LLM`) so the scale test runs the pilot once per model (3B,
  then 7B) and compares b2 — respecting the one-LLM-per-run memory constraint.
  Competence enforcement is togglable (`FAITHFULIDS_ENFORCE_COMPETENCE`;
  report-not-halt for the exploratory pilot). `kaggle/kaggle_pilot_launcher.ipynb`
  repointed to tag `pilot-v2`, N=150, with an appended 7B scale cell.
- **Qwen3-8B scale generator.** Added `configs/llms/qwen3_8b_4bit.yaml`
  (`Qwen/Qwen3-8B`, 4-bit nf4, pinned commit `b968826`, `model_family: qwen` —
  already firewall-disjoint, no firewall change). `TransformersProvider` now
  passes `enable_thinking=False` to `apply_chat_template` **for Qwen3 only**
  (guarded on family + repo name; escape hatch `FAITHFULIDS_QWEN3_THINKING=1`),
  so Qwen3's default `<think>…</think>` reasoning can't consume `max_new_tokens`
  and truncate the explanation into garbage Layer-1 claims. Caveat: 8B-Qwen3 vs
  3B-Qwen2.5 mixes a generation jump with a size jump — "newer+bigger", not pure
  scale. Launcher params repointed to `ref=main` (NON-CITABLE) + `qwen3_8b_4bit`.
- **Pass B — extractor audit (rule-engine).** `RuleAssistedExtractor` gained
  (1) **signed-number direction parsing**: a raw-SHAP dump (`Feature=-7.98`, no
  direction word) now takes its sign from the number instead of defaulting to
  POSITIVE — fixes B0 DSA (0.636 -> 1.0, verified against all 150 cached B0
  explanations); word-driven signs (B1/B3) take precedence and are unchanged;
  (2) **longest-match residual-span guard**: features are matched longest-first
  with consumed spans masked, so a short name no longer double-matches inside a
  longer one (`Packet Length Mean` inside `Fwd Packet Length Mean`). Instrument
  version bumped **1.0.0 -> 1.1.0** via a new required `version` field on the
  extraction config (stamped as `extractor_version`; prompt asset unchanged at
  `prompt.version 1.0.0`). Runs scored by 1.0.0 must be **re-scored** (token-free)
  before their Layer-1 DSA/ARC are trusted; formal EXP-G-001 (300-item human
  audit) must re-pass against 1.1.0 before Tier-A citability.
- **Token-free re-score harness.** `run_pilot` gained a `llm_mode="replay"` +
  `llm_cache_dir` path that serves every generation from a completed run's
  ledger (no provider, no GPU, no tokens) while retraining the detector and
  recomputing TreeSHAP + extraction + metrics under the *current* instruments.
  `tools/rescore_run.py` wraps it: point `FAITHFULIDS_LLM_CACHE_DIR` at a run's
  `_pilot_llm_cache` (matching N/max_rows/llm/seed) to mint a fresh run scored by
  extractor 1.1.0. Smoke-tested live→replay: replay reproduces the live Layer-1
  numbers byte-for-byte with no provider. A self-documenting
  `kaggle/kaggle_rescore_launcher.ipynb` drives it per-model (one cell each,
  no parameter editing) with the DSA litmus and an in-notebook 3-run comparison.
- **Extractor 1.2.0 — participle direction words (blind-audit fix).** The
  63-instance B4@8B "DSA regression" (3B→8B paired sign test p = 1.2e-16) was
  resolved by a 150-item blind-shuffled human audit (`extractor_audit_batch_v1`,
  576/577 claims annotated blind to group) as **Branch 2: instrument artifact**.
  Extractor-error rate 43.3% on the degraded set vs 5.0% control (Fisher
  p = 1.9e-23) while the generated text's directional claims are correct
  essentially everywhere (100% on degraded top-5 claims); every disagreement was
  the extractor emitting "+". Root cause: direction lists held inflected forms
  only, so Qwen3-8B's dominant phrasing "has a **decreasing** effect on the
  attack score" matched no cue and fell to the default-POSITIVE branch
  ("increasing" fell through identically but was accidentally correct). 63/63
  degraded items contain "decreasing" vs 6/63 control — the selection loop that
  *created* the "degraded" label. Fix: direction cues are now stems
  ("increas"/"decreas"/"reduc"/"lower"/"rais"/…); regression test pins the exact
  audit phrase. Instrument version **1.1.0 → 1.2.0** (prompt asset unchanged).
  **Retired claims:** "B4's directional faithfulness degrades with capability"
  and "Layer-1 DSA caught the sign-blind verifier" — both measured the
  extractor. Branches 1/3 falsified: no verifier-trace logging or B4
  regeneration needed. All three pilot runs must be re-scored (token-free
  replay) before any cross-run DSA statement; scoring tooling and the audit
  record live in `extractor_audit_batch_v1\` (`score_audit.py`,
  `scored_human.jsonl`; a second LLM annotator, Meta MUSE, was excluded for
  chance-level agreement κ = 0.02 with 74% spurious "absent" — the exclusion
  itself is audit provenance).
- **Extractor 1.4.0 — paraphrase alias recovery + Gemma 4 extraction model.**
  Qwen3-32B smoke (N=60): 38/60 B3 instances scored structural ZEROS because the
  32B model paraphrases canonical feature names ("the maximum forward packet
  length" for "Fwd Packet Length Max") and exact vocabulary matching finds
  nothing — a mention-DETECTION gap, not unfaithfulness. Fix: (1) hash-pinned
  paraphrase alias table (`configs/extraction_aliases/feature_aliases.yaml`,
  new config family + schema; ~50 features, multi-word high-precision aliases
  only; an alias activates only when its canonical is in the run vocabulary);
  (2) length-preserving match normalisation (case, _/- as spaces) — claim
  windows still slice the lowercase-only view so numeric minus signs survive
  (B0 regression test). Validated on cached corpora: 32B B3 zero-claim
  instances 38 -> 0 (direction agreement on recovered claims 0.944), blind-audit
  agreement vs human unchanged at 99.5%, B0/B1 self-consistency perfect in all
  three N=150 runs. Also repinned the LLM-assisted extraction model
  (rule-assisted fallback unchanged): google/gemma-4-26B-A4B-it @ `5305c1e7`
  (latest Gemma generation, MoE 25.2B/3.8B-active, Apache-2.0, 4-bit, family
  'gemma' still firewall-disjoint) replacing the never-pinned gemma-2-9b-it;
  NOTE it requires a recent transformers v5 (the v5.0 bnb-4bit load regression
  #43032 that hit the 32B pilot is fixed upstream) — smoke-test on Kaggle
  before first LLM-assisted extraction. Instrument version **1.3.0 -> 1.4.0**;
  all runs must be re-scored (token-free replay) before cross-run Layer-1 use.
- **Extractor 1.3.0 — sentence-bounded claim window, nearest cue wins.**
  Follow-up to the 1.2.0 audit: 73/176 Mistral-B4 sign mismatches were direction
  words sitting past the fixed 60-char claim window ("Feature: <long value
  clause>, which decreases the attack score"). The window now extends to the
  next found feature OR the feature's sentence end (terminator lookahead skips
  decimal points; 300-char safety cap), and with sentence-length spans the
  NEAREST direction cue wins instead of NEG-anywhere precedence. Validated on
  cached corpora: blind-audit agreement unchanged at 99.5% (same 3 known
  residuals), B0/B1 exactly 1.000 in all three runs, Mistral-B4 top-5 direction
  agreement 0.524 -> 0.722 (the predicted +73), Mistral-B3 0.971 -> 0.994,
  Qwen3-8B unchanged. The residual Mistral-B4 gap is claims whose sentences
  assert NO direction (extractor defaults POSITIVE) — a metric-design question
  (direction=None / assertion-rate reporting) -> resolved in the same 1.3.0
  instrument version by the evidence field below. Runs must be re-scored
  (token-free replay) before cross-run DSA use.
- **Claim-level `direction_evidence` + DSA decomposition (assertion vs
  reading).** `ClaimTuple` gains an additive optional field recording HOW the
  extractor obtained the direction: `word` / `number` / `llm` / `default`
  (fallback guess); `direction` itself stays mandatory, so no consumer breaks.
  Two additive Layer-1 metrics (file formula_version -> 1.1.0):
  **`dsa_asserted`** — DSA over text-asserted directions only, the pure
  reading-fidelity number and the intended confirmatory directional metric —
  and **`direction_assertion_rate`** — the fraction of present claims whose
  direction the text actually asserts (a generator property; coverage companion,
  always co-reported). Legacy `dsa` is kept as descriptive/continuity (it grades
  the extractor's default guesses against the sign base rate, which is exactly
  how Mistral-B4's "0.55 DSA" arose). Unrecorded evidence (`null`: legacy and
  RQ0 corruption-built claims) counts as ASSERTED so sign-flip corruptions
  cannot escape `dsa_asserted`; fixture and RQ0-guarantee tests added. The
  preregistration must designate `dsa_asserted` (+ rate) as primary before the
  freeze.
- **ε_model per-feature normalisation (set-size confound fixed).** Added
  `comprehensiveness_cited_per_feature` / `sufficiency_cited_per_feature`
  (layer2 file version → 1.2.0, additive; `*_cited` and ε_att unchanged): the raw
  claim-driven ε_model divided by |S| (cited-set size), emitted per k/δ-space
  next to the raw metric. Resolves the **b4 > SHAP-baseline** anomaly — B4 posts a
  larger *raw* `comprehensiveness_cited` than B0 only because it cites fewer,
  verifier-pruned features (|S| ≈ 2.5–3.6 vs 5); **per cited feature** b3 ≈ b4
  (~1.6× B0) and b2 ≈ 0, robust across 3B/7B/8B. Also reframes the **Mistral b4
  "dip"** as a Layer-1 mention-overlap effect (few features cited → lower recall),
  not a causal-faithfulness deficit — its per-feature ε_model is the highest of
  all (0.068). Runs and replay re-scores emit the new metrics automatically.

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
