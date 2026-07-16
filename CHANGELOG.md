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
- **Layer-1 1.2.0 — `dsa_asserted` aggregation fix + top-k directional scope
  (NEXT-QUEUE item 1).** The run-level mean of `dsa_asserted` averaged in a
  structural `0.0` for every instance that asserts no direction, so a generator
  that rarely *commits* to a direction read as directionally unfaithful:
  Mistral-B4 official **0.404** vs claim-level truth **149/150 = 0.993**. Fix
  (**NaN-exclusion at the instance level**): the confirmatory mean now drops
  no-assertion instances — gated on `direction_assertion_rate > 0`, exactly where
  the metric is undefined — while KEEPING genuinely-wrong asserted instances
  (rate > 0, value 0.0) so real sign failures are not hidden. Implemented in
  `analysis.run._instance_values` (a `gate_metric` argument) driving the `mean_ci`
  test, which now also emits `n_instances`; per-instance metric functions still
  return `0.0` (JSON-safe — no `NaN` in artifacts). **Companion scope decision:**
  `dsa` / `dsa_asserted` / `direction_assertion_rate` now grade only claims about
  the attribution's **top-k** features (a full-vocabulary claim was otherwise
  checked against a near-zero SHAP value whose sign is numerical noise), matching
  the mention metrics; `top_k=None` still means all features (back-compat). Chosen
  over claim-level pooling because instance-mean keeps each explanation one vote
  and needs no new per-instance artifact fields. Directional formula versions
  **1.0.0 / 1.1.0 → 1.2.0**; mention / HFR unchanged. **ARC restricted to top-k
  too**, with the same NaN-exclusion: ARC now correlates ranks only within the
  attribution's top-k (out-of-top-k ranks merely separate near-zero SHAP noise),
  and because that can leave `<2` rank-pairs — where Spearman is undefined and the
  code returns a structural 0.0 — a new companion metric **`arc_n_pairs`** counts
  the pairs and the run mean drops instances with `arc_n_pairs < 2` (gated
  `mean_ci`, `gate_min: 2`). B0/B1 stay exactly 1.000 (a perfectly-ordered set's
  top-k subset is still perfectly ordered). New gated analysis configs
  `pilot_dsa_asserted` and `pilot_arc`.
  Validated on the four cached 1.4.0 re-scored runs (NaN-exclusion half; rows are
  pre-top-k): B0/B1 exactly **1.000** at every scale, Mistral-B4 **0.404 → 0.995**,
  every attribution-seeing generator 0.96–1.00, B2 0.60–0.76 at assertion rate
  0.11–0.61. Runs must be re-scored (token-free replay) before cross-run
  `dsa_asserted` use; the preregistration must still designate `dsa_asserted`
  (+ rate) as primary before the freeze.
- **B4/VtE coverage accounting — verifier trace + abstention denominator
  (NEXT-QUEUE item 2).** Verifiers now return a structured
  `VerifierVerdict(supported, call_id, reason, detail)` instead of a bare
  `(bool, str)`, and B4 records it under
  `ExplanationRecord.metadata['verifier_trace']` on both branches (metadata was
  empty, so abstention causes were invisible). RuleVerifier reasons:
  `no_evidence` / `no_cited_feature` / `direction_mismatch` (+ offending feature)
  / `supported`; the LLM Verifier reports the verdict-token pattern. Firewall side
  A stays disjoint (the new `verdict` module imports nothing from `faithfulids`).
  `coverage` / `abstention_rate` are now scoped to **abstention-capable (B4)**
  generations, not all five baselines — the 32B smoke's 24 abstentions over 60 B4
  cells read as **0.08** (24/300) and are now **0.400** (24/60); the two rows carry
  grouping `{scope, generators, n_denominator}`, tokens/latency/$ stay run-global.
- **EXP-G-001 audit record committed + `dsa_asserted` designated primary
  (NEXT-QUEUE item 3).** The blind human extractor audit (`extractor_audit_batch_v1`)
  is now in-repo at `experiments/gates/EXP-G-001_audit_record/` with an
  `AUDIT_RECORD.md` that states plainly it is **interim evidence, not a gate pass**:
  150 items / one human annotator / directional-agreement scoring, vs the formal
  gate's 300 items / two annotators / adjudicated F1 >= 0.95 + Krippendorff alpha.
  So **EXP-G-001 stays `registered`** — the formal dual-annotated run against
  extractor 1.4.0 is still owed before Tier-A citability. Reproduced from the
  committed data: extractor-error **43.3% degraded** (135/238 correct) **vs 5.0%
  control** (Fisher p = 1.9e-23), text directions 100% (degraded) / 99.5% (control),
  all 117 disagreements the default-`+` artifact, 0/576 hedged; the excluded LLM
  annotator (Meta MUSE, kappa 0.02) travels with it as provenance.
  **Prereg designation (pre-freeze — the `prereg-v1` tag is not set yet):**
  `dsa_asserted` is now the confirmatory directional metric across H2/H3,
  co-reported with `direction_assertion_rate`, with legacy `dsa` demoted to
  descriptive. `hypothesis_families.yaml` member `h2_dsa_drop` ->
  `h2_dsa_asserted_drop`; H2/H3 descriptions and the `decision_thresholds.yaml`
  `h2_absolute_drop` description name `dsa_asserted` explicitly.
- **`transformers<5` pinned in the generator launcher + post-pin env capture
  (NEXT-QUEUE item 4).** `kaggle/kaggle_pilot_launcher.ipynb` install cell now pins
  `transformers<5` before it writes `environment.txt` / `env-fingerprint.json`.
  Kaggle ships transformers 5.0.0, whose bnb 4-bit load regressed
  (huggingface/transformers#43032) and crashed the 4-bit generator load — the
  Qwen3-32B run worked around it by hand in a cell that ran *after* the freeze, so
  its exported `environment.txt` recorded 5.0.0 while the run actually used 4.57.6.
  Baking the pin in ahead of the capture removes the manual step and makes the
  provenance file match what runs. `<5` (not the repo's declared `4.46.2`, which
  predates Qwen3 support) resolves to a recent Qwen3-capable 4.x; the exact resolved
  version is recorded post-pin. Replay-only re-scoring loads no model and is
  unaffected; LLM-assisted extraction (Gemma-4) needs v5 and runs in its own session.
- **Capability anchor + session-stats analysis (NEXT-QUEUE item 6).** Two prep
  artifacts for the scaling story. (1) **Capability anchor:**
  `analysis/data/capability_anchor.yaml` maps each pinned generator revision
  (Qwen2.5-3B / Mistral-7B-v0.3 / Qwen3-8B / Qwen3-32B) to parameter count and
  external MMLU / IFEval slots, so the scaling x-axis becomes *measured capability*
  rather than raw parameter count — defusing the newer+bigger / cross-family
  confound of the scale sweep. The benchmark values ship **null (pending, never
  fabricated)**; populate them with harness-matched `lm-eval` numbers over the exact
  pinned revisions (one source for all four). A new `capability_scaling` analysis
  test + `fig_capability_scaling` figure join faithfulness (B2/B3 mention F1) with
  the anchor and stay pending / skip until both the per-model runs are enumerated
  and the anchor is populated. (2) **Session-stats:** a `cost_summary` analysis test
  + `pilot_cost` config surface the run-level cost/throughput aggregates
  (`n_explanations`, `total_tokens`, `mean_latency_ms`, `coverage`,
  `abstention_rate`) already emitted on the cost layer, wired into both Kaggle
  launchers' analysis loops. The pure capability-join core is unit-tested.

- **Multi-class detector — the citability gate (NEXT-QUEUE item 5).** The pilot
  detector collapsed every attack family to `label = (attack_class != "BENIGN")`
  with `binary:logistic`, which on CICIDS2017 is trivially separable (AUC = 1.0,
  macro-F1 = 1.0): explanations of a perfect toy classifier are not interpretable
  evidence, probability-space Layer-2 saturated (comprehensiveness ≈ 0.006 — only
  margin space carried signal), and the per-family recall floor never bit. Built in
  six reviewed steps:
  **(5.1)** a coarsened 8-class target — `BENIGN, DoS, DDoS, PortScan, FTP-Patator,
  SSH-Patator, Web Attack, Bot` — added as an additive `target_class` column
  (DoS/Web variants grouped; Infiltration + Heartbleed excluded as too rare for a
  recall floor); the binary path and the deterministic toy are untouched.
  **(5.1b)** that taxonomy and `kb/attack_classes` were two competing class
  vocabularies that could drift silently and invalidate per-class metrics, so both
  now derive from ONE schema-validated `configs/taxonomy/<dataset>.yaml`;
  validate-configs enforces that every KB class maps to exactly one canonical class
  and that no canonical class is an orphan (a dead `num_class` slot).
  **(5.2)** `predict_proba` returns `(n_samples, n_classes)` for every family
  (binary heads normalised to `[P(BENIGN), P(ATTACK)]`), `class_names` is frozen
  **with** the model and labels those columns positionally, and `predicted_class`
  is the argmax name. `predict_attack_proba` is a deprecated shim defined exactly
  as `1 - P(BENIGN)`, removed after the pilot; internal callers use
  `framework.attack_probability` instead, so the shim has no internal dependents.
  **(5.3 / 5.3b)** multi-class TreeSHAP emits one attribution per class — the old
  `values[-1]` silently explained the LAST class; it now selects the **predicted**
  class per instance, and `AttributionArtifact.explained_class` records which class
  a vector explains (mandatory provenance: without it a multi-class export is
  uninterpretable).
  **(5.4)** Layer-2 measures the class the attribution explains, PINNED from the
  unerased instance and reused for every erased variant (erasure can flip the
  argmax; a delta across two different classes measures nothing);
  `predict_margin` became per-class to match.
  **(5.5)** the gate now asks the stricter K-way question — was it classified as the
  RIGHT family, not merely as *some* attack — and generation is told the argmax
  class name and its probability.
  **(5.6)** `configs/detectors/xgboost_multiclass.yaml` (`multi:softprob`;
  `num_class` derived from the frozen `class_names`, never hard-coded) selects the
  K-way path, which trains on `target_index` and stratifies the explained set on
  `target_class`.
  **Binary continuity is deliberate throughout**: a binary attribution explains the
  attack side for every instance, so Layer-2 keeps measuring that side and the
  `attack`/`benign` prompt strings are unchanged — renaming them would alter every
  LLM request hash and break token-free replay of the cached binary runs. Selecting
  the multi-class detector changes what the generators SEE, so it requires fresh
  generation (not replay) — it defines the full-N Tier-A run rather than preceding it.

- **Multi-class data-coverage review fixes (pre-smoke).** Review of item 5 found two
  defects that would have defeated or crashed the Kaggle multi-class smoke:
  **(a)** the launcher's global `FAITHFULIDS_MAX_ROWS=200000` appends whole CSVs in
  sorted-name order, so only the first day's file loads (the reason every binary
  pilot was BENIGN-vs-DDoS) — a K-way run silently degenerated to 2 classes,
  re-creating the trivially separable task and straddling the
  `len(class_names)==2` binary-continuity branches with per-class SHAP. New
  `rows_per_file` loader option (env `FAITHFULIDS_ROWS_PER_FILE`) takes a
  deterministic evenly-spaced stride per FILE — every day's families survive a
  memory cap, and a stride (not a head) also survives within-day time blocks
  (FTP-Patator morning / SSH-Patator afternoon). `run_pilot` now fails loudly if a
  `multi:*` run resolves to K < 3, and records `max_rows`/`rows_per_file` in the
  resolved config; the multi-class smoke cell swaps the global cap for
  `ROWS_PER_FILE=50000`.
  **(b)** `stratified_explanation_sample` truncated over-quota picks by lowest pool
  index; CICIDS classes are contiguous per-day blocks, so late-day classes could
  vanish from the explained set — and a class then *predicted* but never *true*
  has undefined (`None`) per-class recall, which crashed `evaluate_competence`
  with `TypeError` (even with enforcement off). The K-way path now truncates
  round-robin across classes (each stratum keeps ~n/K; the binary path keeps the
  legacy index truncation byte-for-byte — it is baked into every cached run's
  replay hashes), NA strata no longer consume quota, and a `None` recall now
  FAILS the gate explicitly (recorded as NaN; the remedy is representation, not
  exemption).

- **Multi-class generation wording — predicted-class score labels.** Under the
  K-way detector the attribution explains the PREDICTED class (BENIGN included),
  but every rendered direction was attack-framed: B1 wrote "increased the attack
  score", `ranked_feature_list` rendered "(increases attack score, …)", and the
  b2/b3/b4 prompts instructed directions against "the likelihood of an attack" /
  "the attack score" — false on BENIGN-predicted instances (B1 is the
  faithful-by-construction reference and must never assert a false direction) and
  self-contradictory prompts that risk a class-conditional sign artifact from the
  generator LLM. Fix: additive `GenerationContext.score_label` — the noun of the
  score the attribution explains. Binary runs pass the frozen literal `"attack"`
  (rendered strings and request hashes stay byte-identical: token-free replay of
  every cached run is untouched, pinned by a regression test); K-way runs pass
  the explained class, so B1/`ranked_feature_list` render "increased the BENIGN
  score" (extractor direction stems and the rule verifier's evidence regex parse
  the verbs, not the noun — unchanged). New **v1.1.0 prompt assets** for
  `b2_zeroshot`, `b3_dte_style`, `b4_vte/generator` state directions against the
  `{{predicted_class}}` score (registered in `prompts/REGISTRY.json`; v1.0.0
  untouched); generator configs gain an optional schema-validated
  `prompt_multiclass` ref selected at runtime by `score_label`, and a K-way run
  without one fails loudly. The b4 *verifier* prompt needs no variant (its checks
  are class-agnostic). Deferred, documented: the LLM-assisted extraction prompt
  (`eval_extractor` v1.0.0, unused in the pilot) still defines `+` as "raised the
  attack likelihood" and needs a class-aware semver (audit-gated) before the
  LLM-assisted extraction path activates.

### Metric formula versions / schema

- `configs/metrics/layer2_erasure.yaml`: `1.0.0 → 1.1.0` (additive — new ε_model
  family; ε_att metrics unchanged).
- `configs/metrics/layer1.yaml`: `1.1.0 → 1.2.0`. Directional/rank metrics `dsa` /
  `dsa_asserted` / `direction_assertion_rate` / `arc` gain top-k scope + documented
  NaN-exclusion aggregation (`dsa` and `arc` `1.0.0 → 1.2.0`, the two asserted
  metrics `1.1.0 → 1.2.0`), plus a new companion metric `arc_n_pairs` (`1.2.0`);
  `mention_*` and `hfr` unchanged at `1.0.0`.
- Schema (backward-compatible): `metric.v1.json` gains optional `component` /
  `delta_space`; `detector.v1.json` gains optional `competence_gate`;
  `llm.v1.json` requires `weights.revision` to be a 40-char commit hash (enforced
  going forward; satisfied by the now-pinned configs).

All 122 unit/contract/smoke/determinism tests pass; import-linter (8 contracts),
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
