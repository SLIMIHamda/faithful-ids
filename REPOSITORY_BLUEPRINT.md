# Repository Blueprint — `beyond-plausibility`

**Artifact for:** *Beyond Plausibility: Measuring and Enforcing Faithfulness in LLM-Generated Explanations for Intrusion Detection* (target: Computers & Security).

**Governing dogma:** Scientific rigor and reproducibility take absolute priority over software convenience. Every architectural decision below is justified against that dogma, not against engineering taste.

**Design basis:** Part I (gap analysis), Part II (strategy & positioning), Part III v2 (experimental master plan — tiered anchored design, RQ0 meta-validation, circularity firewall, erasure operator spec, human study v2, statistical protocol).

---

## 0. The Five Load-Bearing Architectural Commitments

Before the tree, the five commitments that everything else hangs from:

1. **The experiment registry is append-only and configuration-complete.** An experiment exists if and only if it has a registered, schema-validated YAML in `experiments/`. Nothing runs without a registry entry; no registry entry is ever edited after its first run (amendments create a new versioned entry that supersedes, never replaces).

2. **`runs/` is a write-once ledger.** Every run writes into a run-ID-addressed directory containing a resolved-config snapshot and a cryptographic manifest. Nothing under `runs/` is ever modified or deleted. Re-execution creates a new run directory. "Raw data is sacred" applies to *all* experiment outputs, not just datasets.

3. **The circularity firewall is enforced by structure, not by discipline.** The VtE internal verifier (`src/faithfulids/generation/b4_vte/verifier/`) and the evaluation claim extractor (`src/faithfulids/extraction/`) live in different packages, use different prompt trees, declare different model families in schema-validated configs, and CI mechanically forbids any import, prompt-hash collision, or model-family overlap between them.

4. **Statistics and figures are pure consumers.** `analysis/` reads only `runs/**` artifacts through a read-only results API; `paper/figures` and `paper/tables` read only `analysis/outputs/**`. Neither can trigger, import, or re-run experiment code. Every figure/table has a spec file that names the exact analysis outputs, run IDs, experiment IDs, and commit it derives from.

5. **Pre-registration is a git event.** Hypothesis families, decision thresholds (H2's ≥10-point drop, H-T's d ≥ 0.4 / ≤5-point deficit), metric definitions, and the human-study analysis plan are committed and tagged (`prereg-v1`) *before* Tier A runs. CI fails any change to pre-registered files after the tag unless it arrives as an explicitly versioned amendment file.

---

## 1. Complete Repository Tree

```
beyond-plausibility/
│
├── README.md                        # what the paper claims; 3-command quickstart per reproduction tier
├── REPRODUCING.md                   # reviewer-facing: the four reproduction tiers (L1–L4), exact commands
├── CITATION.cff                     # citation metadata (paper + artifact DOI)
├── LICENSE                          # code license (MIT/Apache-2.0)
├── LICENSE-ARTIFACTS.md             # per-artifact licensing (prompts, annotations, KB, generated data)
├── CHANGELOG.md                     # versioned artifact history (v1.0 = submission, v1.1 = camera-ready …)
├── Makefile                         # the ONLY sanctioned entry points: make reproduce-l1 … make paper
├── pyproject.toml
├── uv.lock                          # exact, hashed dependency lock
├── environment/
│   ├── Dockerfile                   # pinned base image by digest
│   ├── apptainer.def                # HPC mirror of the Docker image
│   ├── cuda-versions.md             # recorded driver/cuDNN/torch determinism notes
│   └── env-fingerprint.py           # emits the environment hash recorded in every run manifest
│
├── .github/
│   └── workflows/
│       ├── validate-configs.yml     # every config/experiment file against configs/schema/
│       ├── import-contracts.yml     # import-linter layer contracts incl. the firewall
│       ├── firewall-audit.yml       # prompt-hash disjointness, model-family disjointness, no shared code
│       ├── determinism-smoke.yml    # tiny fixed-seed pipeline twice → byte-identical metrics
│       ├── manifest-audit.yml       # every runs/ entry: manifest complete, hashes verify, status terminal
│       ├── prereg-freeze.yml        # pre-registered files unchanged since tag prereg-v1
│       ├── figure-regen.yml         # regenerate all figures/tables from analysis outputs → diff hashes
│       ├── stats-regen.yml          # recompute analysis outputs from run artifacts → diff
│       ├── mapping-completeness.yml # every paper asset in paper/mapping.yaml resolves to COMPLETE runs
│       ├── data-integrity.yml       # dataset + correction-pipeline checksums
│       ├── no-notebook-in-pipeline.yml  # notebooks cannot be imported by, or produce, any pipeline artifact
│       └── docs-build.yml
│
├── configs/                         # ALL parameters live here. Source code contains zero magic constants.
│   ├── schema/                      # JSON Schemas — one per config family; versioned (dataset.v1.json …)
│   ├── datasets/
│   │   ├── cicids2017_corrected.yaml    # Engelen/Lanvin fix pipeline version, split spec, checksums
│   │   ├── cicids2017_raw.yaml          # appendix-only, explicitly flagged non-headline
│   │   ├── unsw_nb15.yaml
│   │   └── cse_cic_ids2018.yaml         # Tier B transfer only — role declared in the config
│   ├── detectors/
│   │   ├── xgboost.yaml                 # anchor detector; exact TreeSHAP admissible
│   │   ├── ft_transformer.yaml          # DeepSHAP, approximate; GPU determinism flags recorded
│   │   └── random_forest.yaml           # Tier B continuity only
│   ├── attribution/
│   │   ├── treeshap.yaml                # removal semantics / background policy pinned here
│   │   └── deepshap.yaml
│   ├── llms/
│   │   ├── mistral_7b_instruct.yaml     # weights hash, revision, quantisation=none
│   │   ├── mistral_7b_instruct_4bit.yaml
│   │   ├── llama31_8b_instruct.yaml
│   │   ├── llama31_8b_instruct_4bit.yaml
│   │   └── frontier_api.yaml            # provider, pinned model snapshot ID, replay-cache policy
│   ├── generators/
│   │   ├── b0_raw_shap.yaml
│   │   ├── b1_template.yaml             # faithful-by-construction; template version pinned
│   │   ├── b2_zeroshot.yaml             # conference method; prompt ref by hash
│   │   ├── b3_dte_style.yaml
│   │   └── b4_vte.yaml                  # KB version, verifier model family, threshold ref, abstention policy
│   ├── extraction/
│   │   └── eval_extractor.yaml          # fixed model (family ≠ any generator/verifier), frozen prompt hash, T=0
│   ├── corruption/
│   │   └── rq0_operators.yaml           # fabricated-feature, sign-flip, rank-inversion, omission,
│   │                                    #   magnitude-inflation, vague-substitution; injection counts
│   ├── metrics/
│   │   ├── layer1.yaml                  # mention P/R/F1, DSA, ARC, HFR — formula versions
│   │   ├── layer2_erasure.yaml          # primary: conditional-expectation imputation (per-class kNN/gen model);
│   │   │                                #   secondary: retrain-ROAR (anchor only); k ∈ {1,3,5}
│   │   └── plausibility_judge.yaml      # judge model family (∉ explainer families), validation gate ρ ≥ 0.6
│   ├── sampling/
│   │   ├── n400_stratified.yaml         # 400/dataset, per-class stratification, minority floor 30
│   │   └── stochasticity_k3.yaml        # 100-instance subsample, k=3 generations, operating temperature
│   ├── statistics/                      # PRE-REGISTERED — frozen at tag prereg-v1
│   │   ├── hypothesis_families.yaml     # H0,H1,H2,H3,H-T,H4 memberships for Holm–Bonferroni
│   │   ├── decision_thresholds.yaml     # H2 ≥10pt; H-T d ≥ 0.4 & ≤5pt deficit; RQ0 sens/spec ≥ .9
│   │   ├── tests.yaml                   # Friedman+Nemenyi, Wilcoxon, bootstrap CI params, mixed-effects spec
│   │   └── amendments/                  # versioned deviations, each with rationale + date (append-only)
│   └── seeds/
│       └── seed_table.yaml              # explicit per-experiment, per-cell, per-stage seeds — committed
│
├── prompts/                         # prompts are versioned scientific instruments, not strings in code
│   ├── REGISTRY.json                # name → semver → sha256 → frozen flag; CI verifies hashes
│   ├── generation/
│   │   ├── b2_zeroshot/v1.0.0.md
│   │   ├── b3_dte_style/v1.0.0.md
│   │   └── b4_vte/
│   │       ├── generator/v1.0.0.md
│   │       └── verifier/v1.0.0.md   # firewall side A
│   ├── extraction/
│   │   └── eval_extractor/v1.0.0.md # firewall side B — CI enforces hash + wording disjointness from side A
│   └── judging/
│       └── plausibility/v1.0.0.md
│
├── kb/                              # feature-semantics knowledge base (VtE grounding source)
│   ├── schema/kb.v1.json
│   ├── feature_semantics/           # per-dataset feature dictionaries (flow features → meaning, units, ranges)
│   ├── attack_classes/              # per-dataset attack-class descriptions
│   ├── cti/                         # OPTIONAL ATT&CK/CTI snapshot for the single exploratory ablation cell
│   │   └── SNAPSHOT.md              # frozen retrieval corpus version + date (CTI drifts; snapshot doesn't)
│   └── VERSIONS.md                  # KB semver history; configs reference KB by version + hash
│
├── data/                            # payloads DVC-tracked; pointers + manifests in git. NEVER code here.
│   ├── raw/                         # as-downloaded, read-only, checksummed. Never modified, never committed
│   │   ├── cicids2017/  ├── unsw_nb15/  └── cse_cic_ids2018/
│   ├── corrected/                   # output of the deterministic correction pipeline (Engelen/Lanvin)
│   │   └── cicids2017/ + CORRECTIONS_APPLIED.md + input/output checksums
│   ├── processed/                   # feature matrices per dataset-config version
│   ├── splits/                      # frozen train/dev/test + explanation-set index files (row-level, committed)
│   │   └── */split_manifest.json    # seed, stratification spec, class counts, source data hash
│   └── cache/                       # expensive intermediates, content-addressed, provenance-stamped
│       ├── attributions/            # SHAP arrays keyed by (model hash, data hash, attribution config hash)
│       └── llm_calls/               # append-only request/response ledger: request hash, full payload,
│                                    #   model snapshot ID, timestamp, latency, tokens — enables L3 replay
│
├── models/                          # frozen trained detector artifacts (DVC), one dir per training run
│   └── xgboost__cicids2017c__seed42/
│       ├── model.bin  ├── MANIFEST.json  └── training_metrics.json
│
├── src/faithfulids/                 # the library. Layered; import contracts enforced in CI.
│   ├── framework/                   # L0 — formal spine. Claim tuple schema (feature, direction, rank,
│   │   │                            #   magnitude), explanation record schema, ε_nar/ε_att decomposition
│   │   │                            #   definitions, generator/metric interfaces. Pure; no I/O, no deps.
│   │   ├── schemas.py  ├── decomposition.py  └── interfaces.py
│   ├── provenance/                  # L0 — manifest writer/verifier, hashing, run-ID minting, lineage records
│   ├── datasets/                    # L1 — loaders, correction pipeline, split materialisation
│   │   ├── corrections/             #   Engelen/Lanvin fixes as deterministic, tested, versioned transforms
│   │   └── loaders/
│   ├── detectors/                   # L2 — model definitions + training entrypoints. Training writes frozen
│   │   │                            #   artifacts to models/; evaluation code loads frozen artifacts ONLY.
│   │   ├── xgboost/  ├── ft_transformer/  └── random_forest/
│   ├── attribution/                 # L2 — TreeSHAP (exact), DeepSHAP (approx); common Attribution artifact
│   │   ├── base.py  ├── treeshap/  └── deepshap/
│   ├── llm/                         # L2 — provider-agnostic client: caching, retry, full call logging,
│   │   │                            #   pinned snapshot enforcement, replay mode (cache-only, no network)
│   ├── generation/                  # L3 — one subpackage per generator; adding B5 = new subpackage + config
│   │   ├── b0_raw_shap/  ├── b1_template/  ├── b2_zeroshot/  ├── b3_dte_style/
│   │   └── b4_vte/
│   │       ├── kb_retrieval.py  ├── generator.py  ├── abstention.py
│   │       └── verifier/            # FIREWALL SIDE A — may never be imported outside b4_vte
│   ├── extraction/                  # L3 — FIREWALL SIDE B — evaluation claim extractor. No imports from
│   │   │                            #   generation.*; own prompts; own model family; validated on audit set
│   ├── corruption/                  # L3 — RQ0 operators over B1 outputs; emit ground-truth corruption labels
│   ├── metrics/                     # L4 — consumes framework schemas + extracted claims + attributions.
│   │   │                            #   STRUCTURALLY BLIND to which generator produced an explanation.
│   │   ├── layer1/                  #   mention P/R/F1, DSA, ARC, HFR
│   │   ├── layer2/                  #   comprehensiveness/sufficiency + erasure operators (cond-exp, ROAR)
│   │   ├── meta/                    #   RQ0 sensitivity/specificity/ROC vs corruption ground truth
│   │   ├── plausibility/            #   LLM-judge harness + human-rating ingestion (plausibility ONLY)
│   │   └── cost/                    #   latency, $/explanation, tokens, abstention/coverage accounting
│   ├── orchestration/               # L5 — registry loader, cell expansion, seed control, stage runner,
│   │   │                            #   gate enforcement (extractor-audit gate, RQ0 gate), manifest emission
│   └── results/                     # L5 — the READ-ONLY results API: load runs/** by run ID, verify hashes.
│                                    #   The ONLY src module analysis/ may import.
│
├── experiments/                     # the append-only experiment registry (one YAML per experiment)
│   ├── REGISTRY.md                  # human-readable index: ID, RQ/hypothesis, status, superseded-by
│   ├── ANCHOR.yaml                  # the anchor configuration, defined once, referenced everywhere
│   ├── gates/
│   │   ├── EXP-G-001_extractor_audit.yaml   # 300-item dual-annotation audit; gate F1 ≥ .95, report α
│   │   └── EXP-G-002_rq0_calibration.yaml   # corruption calibration; gate: per-metric sens/spec ≥ .9
│   ├── tier_a/
│   │   └── EXP-A-001_core_factorial.yaml    # 2×2×(2+3×3) = 44 cells; refs sampling, seeds, metrics
│   ├── tier_b/
│   │   ├── EXP-B-001_transfer_ids2018.yaml
│   │   ├── EXP-B-002_quantisation.yaml
│   │   ├── EXP-B-003_detector_continuity_rf.yaml
│   │   └── EXP-B-004_sensitivity_sweeps.yaml   # top-k {3,5,8}, temp {0,.7}, verifier threshold ×3
│   ├── stochasticity/
│   │   └── EXP-S-001_generation_variance.yaml  # 100-instance × k=3 protocol
│   ├── human_study/
│   │   └── EXP-H-001_triage_study.yaml         # links preregistration DOI, materials build, conditions
│   └── exploratory/
│       └── EXP-X-001_cti_rag_anchor.yaml       # single cell, schema-flagged exploratory=true → CI blocks
│                                               #   any headline figure from citing it
│
├── runs/                            # WRITE-ONCE run ledger. Payloads DVC-tracked; manifests in git.
│   └── EXP-A-001/
│       └── EXP-A-001__a1b2c3d__2026-08-12T0930Z/
│           ├── MANIFEST.json        # see §6 — full provenance closure
│           ├── config.resolved.yaml # every reference flattened; the run is reconstructible from this alone
│           ├── STATUS               # RUNNING → COMPLETE | FAILED (terminal states immutable)
│           ├── artifacts/
│           │   ├── attributions/…parquet
│           │   ├── explanations/…jsonl      # per instance: text, generator, llm_call_ids, abstention flag
│           │   ├── claims/…jsonl            # extractor output, extractor version + prompt hash stamped
│           │   ├── metrics/…parquet         # per-instance and per-cell
│           │   └── llm_log_index.json       # pointers into data/cache/llm_calls
│           └── logs/
│
├── analysis/                        # statistics — pure consumer of runs/**, producer for paper/
│   ├── configs/
│   │   └── h1_gap.yaml …            # each names: hypothesis, EXACT run IDs, test refs, threshold refs
│   ├── src/                         # friedman_nemenyi.py, wilcoxon_pairs.py, bootstrap_ci.py,
│   │   │                            #   mixed_effects.py, coverage_risk.py, variance_components.py
│   ├── outputs/                     # one dir per analysis config: results.parquet/json + MANIFEST.json
│   │   └── h1_gap__r4e5f6a__2026-09-02/
│   └── error_taxonomy/              # failure-mode coding scheme + coded instances (annotated, versioned)
│
├── human_study/                     # everything human-subjects, isolated for ethics review
│   ├── preregistration/             # frozen PDF of OSF prereg + DOI + registration timestamp
│   ├── ethics/                      # IRB approval (redacted), consent forms, debriefing script
│   ├── instruments/                 # task interface spec, response forms, training materials
│   ├── materials_build/             # config + spec for building the 4 condition sets from run artifacts,
│   │   │                            #   incl. surface-matching procedure (±10% length, hedging, readability)
│   │   └── manipulation_check/      # independent-rater indistinguishability results
│   ├── data/
│   │   ├── raw_deidentified/        # immutable, checksummed
│   │   └── processed/
│   └── synthetic_sample/            # fake responses matching the schema → reviewers test the pipeline
│
├── paper/
│   ├── manuscript/                  # LaTeX source; \includegraphics ONLY from figures/generated/
│   ├── mapping.yaml                 # MASTER TRACEABILITY MATRIX: every figure/table/claim →
│   │                                #   analysis outputs → run IDs → experiment IDs → commit
│   ├── figures/
│   │   ├── specs/fig_cd_diagram.yaml …     # declarative: inputs, script, expected output hash
│   │   ├── src/fig_cd_diagram.py …         # one script per figure; reads analysis/outputs ONLY
│   │   └── generated/                      # regenerated by `make figures`; CI diffs against committed
│   ├── tables/
│   │   ├── specs/  ├── src/  └── generated/   # same pattern; LaTeX tables emitted, never typed
│   └── supplementary/               # appendix assets, per-class error tables, full prompt listings (generated)
│
├── artifact/                        # the release layer reviewers touch first
│   ├── REPRODUCIBILITY_CHECKLIST.md # ACM Artifact Review / NeurIPS checklist, filled, cross-linked
│   ├── AVAILABILITY.md              # DOIs (Zenodo code+runs snapshot, OSF prereg+human-study), licenses,
│   │                                #   dataset access instructions (raw sets not redistributable)
│   ├── zenodo.json                  # deposit metadata
│   ├── release_manifest.py          # builds the release bundle; verifies closure (no dangling references)
│   └── reviewer_kit/                # L1 quickstart: pinned container + analysis outputs → all figures, <30 min
│
├── docs/
│   ├── architecture.md              # this blueprint, maintained
│   ├── experiment-lifecycle.md      # §5 of this document, expanded, with diagrams
│   ├── dependency-graph.md          # layer rules + import-linter contract listing
│   ├── firewall.md                  # the circularity firewall: rationale, rules, mechanical enforcement
│   ├── lineage.md                   # artifact lineage model + manifest schema reference
│   ├── configuration.md             # config philosophy, schema versioning, how references resolve
│   ├── registering-experiments.md   # the workflow: propose → schema-validate → register → tag → run
│   ├── reproducibility-guide.md     # tiers L1–L4, expected runtimes, hardware, tolerance policy
│   ├── reviewer-guide.md            # "verify Table 3 in 10 minutes" recipes
│   ├── naming-conventions.md        # IDs for experiments, runs, prompts, KB, datasets, figures
│   ├── coding-standards.md
│   └── contributing.md              # incl. what is FORBIDDEN (editing runs/, unregistered experiments…)
│
├── tests/
│   ├── unit/                        # per module; metrics tested against hand-computed fixtures
│   ├── metrics_fixtures/            # tiny worked examples with known-correct metric values (in git)
│   ├── determinism/                 # same seed → byte-identical outputs, per stage
│   ├── contracts/                   # import-layer tests, firewall tests, schema round-trips
│   └── pipeline_smoke/              # 5-instance end-to-end on a toy slice, runs in CI
│
├── notebooks/                       # QUARANTINE ZONE — exploration only. CI forbids pipeline imports from
│   │                                #   here and forbids any runs/analysis/paper artifact citing a notebook.
│   └── exploratory/
│
└── tools/                           # repo self-auditing (not experiment code)
    ├── audit_manifests.py           # walk runs/: verify hashes, completeness, immutability (mtime ledger)
    ├── lineage_graph.py             # render the artifact DAG for any figure/table/claim
    ├── firewall_check.py            # prompt-hash disjointness, model-family disjointness, import scan
    ├── prereg_diff.py               # diff pre-registered files against tag prereg-v1
    └── release_closure.py           # verify release bundle references resolve (no dangling run IDs)
```

---

## 2. Directory Contracts

For each directory: why it exists, its scientific responsibility, boundaries (what may / may not live there), interactions, inputs, outputs.

### `configs/`
- **Why:** Principle 1 (experiment immutability) requires that every parameter be externalized, schema-validated, and referenceable by hash. This is the single source of scientific parameters.
- **Responsibility:** Define the *space* of admissible experiments. Encode pre-registered statistical commitments.
- **May contain:** YAML configs, JSON Schemas, the seed table, pre-registration amendments.
- **May NOT contain:** code, defaults duplicated from code (code has no defaults for scientific parameters — a missing config key is a hard error, never silently defaulted), results, paths to machines.
- **Interactions:** referenced by `experiments/` entries; resolved and snapshotted by `orchestration` into each run; `statistics/` subtree is consumed by `analysis/` and frozen by the prereg CI gate.
- **Inputs:** human authorship, schema validation. **Outputs:** resolved config snapshots inside runs.

### `prompts/`
- **Why:** In this paper prompts are *scientific instruments* (the generator axis IS the paper; the extractor is "the hidden instrument", Part III §3.2). Instruments must be versioned, frozen, and hash-addressed.
- **Responsibility:** Immutable, semver'd prompt texts with a hash registry; structural separation of generation vs extraction vs judging prompt trees (firewall).
- **May contain:** prompt files, the registry. **May NOT contain:** code, f-string templates assembled at runtime outside the registered files, unfrozen "working" prompts (drafts live in `notebooks/`).
- **Interactions:** referenced by hash from `configs/generators`, `configs/extraction`, `configs/metrics/plausibility_judge`; hash-verified by CI and at run time.

### `kb/`
- **Why:** VtE's grounding source. A retrieval corpus that silently drifts destroys reproducibility of B4; the KB must be a versioned artifact like a dataset.
- **Responsibility:** Frozen feature-semantics dictionaries, attack-class knowledge, and the optional CTI snapshot (exploratory cell only).
- **Boundaries:** no retrieval *code* (that is `generation/b4_vte/kb_retrieval.py`); no live-updated CTI feeds — snapshots only, with date and hash.

### `data/`
- **Why:** Principle 3 (raw data is sacred) plus the benchmark-correction contribution: the corrected-CICIDS2017 pipeline is itself a reviewable scientific claim.
- **Responsibility:** Four strata with strictly one-directional flow: `raw → corrected → processed → splits`, plus `cache/` for expensive intermediates.
- **May contain:** data payloads (DVC-tracked), checksums, split index files (committed to git — they are small and load-bearing), the LLM call ledger.
- **May NOT contain:** code, manually edited files of any kind, anything written by a human.
- **Key rules:** `raw/` is read-only after checksum registration. `corrected/` is produced only by the versioned correction pipeline in `src/faithfulids/datasets/corrections` and records the exact fix-set applied. `cache/` entries are content-addressed by the hash of everything that produced them; a cache entry never "updates" — a changed input yields a new key. The `llm_calls/` ledger is append-only and is what makes reproduction tier L3 (deterministic replay without GPU/API access) possible.

### `models/`
- **Why:** The requirement "detectors without mixing training and evaluation logic" is realized as an *artifact boundary*: training produces frozen model files here; everything downstream loads frozen artifacts and can never retrain implicitly.
- **Responsibility:** Frozen detector weights + training manifests (data hash, config hash, seed, environment hash, training metrics).
- **May NOT contain:** models without manifests; overwritten models (new training = new directory).

### `src/faithfulids/`
- **Why:** The library exists to *serve the registry*, not the other way around. Layering (§5) guarantees the isolation the master plan demands: metrics never see generators; the verifier never touches evaluation.
- **Responsibility per subpackage:** stated in the tree. Three deserve emphasis:
  - `framework/` is the paper's §3 in code: claim schema, the ε_model ≲ ε_nar + ε_att decomposition, and abstract interfaces. It is dependency-free so that its definitions cannot be contaminated by implementation concerns.
  - `extraction/` (firewall side B) may not import from `generation` and its prompts/model family are disjoint from VtE's verifier by CI-enforced contract. Its validity is established by the gate experiment EXP-G-001 — orchestration refuses to compute Layer-1 metrics for any run that does not reference a passing extractor-audit run ID.
  - `metrics/` receives `(claims, attribution, detector-outputs, erasure-operator-config)` and returns numbers. The function signatures make it *impossible* to pass "which generator wrote this" — generator identity exists only as an opaque grouping key added afterwards by orchestration. This is Principle "metrics never depend on a specific generation method" enforced by type, not by convention.
- **May NOT contain:** file paths, dataset names, model names, thresholds, prompt text (all come from configs); `utils/`, `common/`, `misc/` (forbidden names — every module has a scientific responsibility or it does not exist).

### `experiments/`
- **Why:** Principle 2 (traceability). The registry is the authoritative answer to "which configuration generated this?".
- **Responsibility:** One YAML per experiment, composing configs by reference; declares its research question, hypothesis family, gates it depends on, seed-table section, and tier. `ANCHOR.yaml` defines the anchor cell once — Tier B entries reference it rather than restating it (a restated anchor that drifts is a classic irreproducibility bug).
- **Boundaries:** append-only; a change to a run experiment = new entry with `supersedes:` field; `exploratory/` entries carry a schema flag that CI uses to block them from headline paper assets.

### `runs/`
- **Why:** The write-once ledger; Principles 1–3 simultaneously.
- **Responsibility:** Complete, immutable, hash-manifested record of every execution.
- **May NOT ever happen here:** modification, deletion, manual file placement, "cleanup". Failed runs remain with `STATUS=FAILED` — negative provenance is provenance.
- **Inputs:** orchestration only. **Outputs:** consumed by `analysis/` via the `results` read-only API.

### `analysis/`
- **Why:** "Statistics consume experiment outputs, never rerun experiments" — enforced by dependency direction: `analysis/` may import only `faithfulids.results` and `faithfulids.framework` (schemas).
- **Responsibility:** Hypothesis-addressed statistical pipelines. Each analysis config enumerates the exact run IDs it consumes (no glob patterns — globbing over runs is silent selection bias) and references pre-registered tests and thresholds by config path.
- **Outputs:** manifested analysis outputs, one directory per (analysis config, commit) pair — analysis outputs are themselves immutable artifacts with lineage.

### `human_study/`
- **Why:** RQ5/H4 evidence plus ethics isolation; the surface-matching build (fluency/length confound control) must be as reproducible as any compute experiment.
- **Responsibility:** Preregistration freeze, instruments, condition-set build spec (which consumes run artifacts and applies the RQ0-style corruptions + surface matching), manipulation-check results, de-identified data.
- **Boundaries:** no identifiable data ever; raw de-identified responses immutable; analysis lives in `analysis/` (h4 config), not here — this directory holds *evidence*, not computation.

### `paper/`
- **Why:** Principle 4 (figures are generated) and Principle 5 (paper first). `mapping.yaml` is the artifact reviewers will actually check: every figure, table, and headline claim maps to analysis outputs → run IDs → experiment IDs → commit.
- **Boundaries:** `generated/` is written only by figure/table scripts; the manuscript may include graphics only from `generated/`; a figure spec whose expected-hash mismatches the committed PDF fails CI. No hand-drawn, hand-edited, or externally produced graphics anywhere.

### `artifact/`, `docs/`, `tests/`, `tools/`, `notebooks/`
- `artifact/`: the release closure — checklist, DOIs, licenses, reviewer kit; `release_closure.py` guarantees the bundle has no dangling references (every run ID cited by the paper is present in the deposited snapshot).
- `docs/`: documentation as a first-class contribution — each file listed in the tree corresponds to one of the documentation-philosophy requirements.
- `tests/`: correctness of the *instruments* (metric fixtures with hand-computed values are the unit-test analogue of RQ0), determinism, contracts.
- `tools/`: the repository audits itself; these scripts back the CI gates.
- `notebooks/`: quarantine. Exploration is legitimate; letting it touch the pipeline is not.

---

## 3. Design Rationale (reproducibility-first justifications)

1. **Registry + resolved-config snapshot, not "config files + CLI flags".** CLI flags are invisible parameters — the exact failure mode Principle 1 forbids. Here the runner accepts exactly one argument (an experiment ID); everything else is resolved from the registry and snapshotted into the run. The snapshot means the run is reconstructible even if `configs/` later evolves.

2. **Two-sided firewall by package boundary.** The master plan calls the "VtE graded by its own verifier" objection the single most dangerous methodological attack. A policy statement in a README does not survive hostile review; a package structure with CI-enforced import contracts, disjoint prompt trees with hash checks, and schema-level model-family disjointness does — and it gives the methods section a checkable sentence: *"enforced mechanically in the released artifact (CI job `firewall-audit`)"*.

3. **Gates as first-class experiments.** The extractor audit (F1 ≥ 0.95) and RQ0 calibration (sens/spec ≥ 0.9) are not preprocessing chores; they are registered experiments whose passing run IDs are *referenced as dependencies* by every downstream experiment. Orchestration refuses to compute Layer-1 metrics without a passing gate reference. The plan's "metrics failing H0 are repaired or dropped before the main sweep" becomes a mechanical ordering constraint, not a promise.

4. **Generator identity is opaque to metrics by construction.** Metric functions cannot receive generator identity; grouping happens after computation. This converts "metrics should never depend on a specific generation method" from a review-time hope into a compile-time property.

5. **B0/B1 are LLM-independent in the cell expansion.** The orchestrator's cell-expansion logic reads generator configs' `llm_dependent: false` flag, yielding the 2+3×3=11 cells per dataset×detector exactly as the plan counts them — the cell arithmetic in the paper and the artifact provably match.

6. **Append-only LLM ledger = the reproducibility answer for nondeterministic dependencies.** Frontier API models are deprecated, and even temperature-0 API calls are not bit-stable. The ledger (full request/response with model snapshot IDs) makes every published number replayable forever (tier L3), and honest: the paper can state which numbers are replay-verifiable vs re-executable.

7. **Splits and seeds in git, payloads in DVC.** Row-level split indices and the full seed table are tiny and load-bearing → git. Data payloads and run artifacts are large → DVC with a Zenodo-deposited remote snapshot at release. Manifests and hashes always live in git, so integrity is verifiable even without pulling payloads.

8. **Statistics pinned to enumerated run IDs.** Glob-based run selection lets a re-run silently replace the sample under a test. Enumerated IDs make the evidence set for every hypothesis explicit, diffable, and reviewable.

9. **Pre-registration as a git tag with a CI freeze.** "Pre-registered thresholds" is only credible if the artifact can show the thresholds predate the results. The `prereg-v1` tag timestamp + `prereg-freeze.yml` + append-only amendments directory provide exactly that evidence chain, aligned with the OSF preregistration DOI.

10. **Paper-shaped top level.** `framework → datasets/detectors/attribution → generation → extraction/corruption → metrics → experiments → analysis → paper → artifact` reads as Problem formulation → Methods → Experiments → Metrics → Statistics → Figures/Tables → Release. A reviewer can navigate the repository with the paper's table of contents in hand. There is deliberately no `utils/`.

---

## 4. Experiment Lifecycle (configuration → published figure)

Illustrated with the Tier A core factorial feeding the H1 headline (the plausibility–faithfulness gap) and its critical-difference diagram.

**Stage 0 — Prerequisites (gates).**
`EXP-G-001` (extractor audit): 300 stratified explanations dual-annotated; extractor P/R/F1 vs adjudicated gold + Krippendorff's α computed; run completes with `gate: PASSED` in its manifest. `EXP-G-002` (RQ0 calibration): corruption operators applied to B1 outputs; per-metric ROC/sensitivity/specificity + fluency-correlation computed; passing metric set recorded. Both run IDs become mandatory references for Stage 3+.

**Stage 1 — Registration.**
Author writes `experiments/tier_a/EXP-A-001_core_factorial.yaml` composing dataset/detector/attribution/LLM/generator/sampling/metric configs by reference, citing the seed table section, hypothesis family (H1, H2), and gate dependencies. PR triggers `validate-configs` + `mapping-completeness`. Merge = registration. Registry entry is now immutable.

**Stage 2 — Execution.**
`make run EXP=EXP-A-001`. Orchestration: resolves and snapshots the config; verifies environment fingerprint against the lock; verifies gate references; mints run ID `EXP-A-001__<git-sha>__<utc>`; expands 44 cells; executes stages *(load frozen split → load frozen detector → compute/reuse cached attributions → generate explanations (LLM calls through the logging client) → extract claims (firewalled extractor) → compute Layer-1/Layer-2/plausibility/cost metrics)*; writes artifacts + `MANIFEST.json`; sets `STATUS=COMPLETE`. Any parameter not in the snapshot cannot influence the run — the runner has no other inputs.

**Stage 3 — Statistical analysis.**
`analysis/configs/h1_gap.yaml` enumerates the exact run IDs, references pre-registered tests (Friedman + Nemenyi, Wilcoxon pairs, bootstrap CIs, Holm–Bonferroni within family H1) and thresholds. `make analyse H=h1_gap` loads artifacts through the read-only results API (hash-verified), computes, writes a manifested output directory.

**Stage 4 — Figure/table generation.**
`paper/figures/specs/fig_cd_diagram.yaml` names its analysis-output directory and script. `make figures` regenerates `generated/fig_cd_diagram.pdf`; the spec's expected hash is updated in the same commit; CI re-runs the generation and diffs.

**Stage 5 — Paper assembly & traceability.**
`paper/mapping.yaml` gains the row: `Figure 4 → fig_cd_diagram → analysis h1_gap__<sha> → runs [EXP-A-001__…] → experiments [EXP-A-001] → gates [EXP-G-001, EXP-G-002]`. `mapping-completeness` CI verifies every cited run exists, is COMPLETE, is non-exploratory, and hash-verifies.

**Stage 6 — Release.**
`release_closure.py` assembles the Zenodo bundle: code at the release tag, manifests, analysis outputs, run artifacts (or L3-sufficient caches), and verifies closure. `REPRODUCING.md` tiers let a reviewer verify Figure 4 from analysis outputs in minutes (L1), from run artifacts (L2), from the LLM ledger (L3), or from scratch (L4).

**Failure path.** A failed run keeps its directory and FAILED status forever; the fix is a code/config change (new commit, possibly a superseding registry entry) and a *new* run. History is never rewritten.

---

## 5. Dependency Graph and Import Contracts

Layers (a layer may import strictly downward; enforced by import-linter in CI):

```
L0  framework, provenance                (pure definitions; import nothing internal)
L1  datasets                             (→ L0)
L2  detectors, attribution, llm          (→ L1, L0)
L3  generation, extraction, corruption   (→ L2, L1, L0)
L4  metrics                              (→ L0 schemas, L2 attribution/detector artifacts; NOT L3 generation)
L5  orchestration, results               (→ everything below)
──── repository boundary ────
A   analysis/                            (→ faithfulids.results + faithfulids.framework ONLY)
P   paper/figures, paper/tables          (→ analysis/outputs files ONLY; no faithfulids imports at all)
```

**Named forbidden edges (each is a CI contract):**
1. `metrics.* → generation.*` — metrics blind to generators (isolation requirement).
2. `extraction.* ↔ generation.b4_vte.verifier.*` — the circularity firewall, both directions, plus: no shared modules, prompt-hash disjointness, model-family disjointness (schema-checked).
3. `generation.* → metrics.*` — generators may not peek at how they will be scored (with the sole audited exception that VtE's *verifier* implements its own checking logic internally — never by importing evaluation code).
4. `analysis → orchestration | generation | llm` — statistics can never rerun experiments; the results API exposes no execution capability.
5. `anything → notebooks/` and `notebooks → runs-writing paths`.
6. `detectors` evaluation paths → training entrypoints (frozen-artifact boundary: inference code cannot trigger training).
7. `framework → anything internal` — the theory layer stays pure.

No cycles are possible: the graph is a DAG by construction, and the two firewalled L3 siblings are mutually non-importing.

---

## 6. Data Lineage and Provenance Model

**Universal rule:** every artifact directory (dataset stratum, model, cache entry, run, analysis output, generated figure) carries a `MANIFEST.json` conforming to `provenance/manifest.v1.json`:

```
identity      : artifact ID, type, schema version
producer      : experiment ID (if any), pipeline stage, code version = git commit + dirty-flag (dirty runs are
                REFUSED by the runner outside a debug mode that stamps NON-CITABLE)
configuration : resolved-config snapshot hash (+ the snapshot itself for runs)
inputs        : list of {artifact ID, content hash} for EVERY input — datasets, splits, models, KB version,
                prompt hashes, gate run IDs, upstream caches
environment   : lock-file hash, container image digest, hardware (GPU model, driver, cuDNN), OS
randomness    : every seed consumed, keyed by stage and cell (from the committed seed table)
models        : detector artifact hashes; LLM identities as {weights sha / API snapshot ID, quantisation,
                revision}; extractor & judge identities likewise
timestamps    : start/end UTC
outputs       : file list with sha256 each
status        : COMPLETE | FAILED (terminal, immutable)
```

**Lineage closure.** Because every manifest's `inputs` are (ID, hash) pairs, `tools/lineage_graph.py` reconstructs the full DAG behind any paper asset: *Figure 4 → analysis h1_gap → runs → {splits → corrected → raw checksums; models → training runs; prompts vX @hash; KB vY @hash; extractor-audit gate run; seed table §; commit; container digest}*. This is the mechanical answer to every question in Principle 2 (which config? model? seed? split? commit? prompts? verifier? extraction model? metrics? statistics?).

**Specific instruments tracked as versioned inputs:** prompt versions (registry hash), KB version, correction-pipeline version, erasure-operator config (operator type + imputation-model fit hash — the fitted imputation model is itself a manifested cache artifact), corruption-operator config with per-instance ground-truth labels, judge identity + its validation-run reference, and the human-study materials build (which explanation instances, which corruptions, surface-matching parameters, manipulation-check results).

**Nothing is silently regenerated:** cache lookups are by content-address of all inputs; a hash miss creates a *new* entry and the manifest of the consumer records which entry it used.

---

## 7. Scalability (extension without redesign)

| Extension | What is added | What is edited |
|---|---|---|
| New dataset (CIC-IoT2023, NF-v2) | `configs/datasets/*.yaml`, KB feature dictionary, split manifest | nothing |
| New detector | `src/faithfulids/detectors/<name>/` implementing the L2 interface + config | nothing else — training/eval boundary and manifests come from the framework |
| New attribution method | subpackage under `attribution/` + config; must declare exact-vs-approximate (the ε_att bookkeeping consumes this flag) | nothing |
| New generator (B5, agentic VtE) | subpackage under `generation/` + config + prompt tree | **zero evaluation code** — metrics are structurally generator-blind |
| New metric | module under the appropriate `metrics/` layer + formula version in `configs/metrics/` + hand-computed fixture + **an RQ0 calibration entry** (the meta-validation study is reusable infrastructure: a new metric is admissible only after passing the corruption battery) | nothing |
| New human study | new `experiments/human_study/` entry + `human_study/` instruments + prereg amendment | nothing |
| Follow-up papers (P5 agentic, P6 adversarial) | P6's threat model = new corruption/perturbation subpackage + Tier-B-style registry entries; P5 = new generator + new outcome metrics. Either can also fork the repo template — `framework/`, `provenance/`, orchestration, the registry pattern, and CI transfer wholesale | no architectural change |

The deferred axes (§10 of the master plan) already have named landing sites: IoT datasets → `configs/datasets/`; CTI-RAG → promoted from `experiments/exploratory/`; adversarial robustness → sibling of `corruption/`.

---

## 8. Hostile Reproducibility Audit (self-review) and Remediations

Acting as a hostile Computers & Security / ACM-artifact reviewer:

**A1. "Your frontier API model will not exist in two years."** Correct; execution-reproducibility of that axis is unattainable. **Remediation (adopted):** tier L3 replay via the append-only LLM ledger with pinned snapshot IDs; the paper's reproducibility statement labels API-model numbers *replay-verifiable*, open-weights numbers *re-executable*; CI runs an L3 replay smoke test proving cache-only mode produces published metrics.

**A2. "Temperature 0 is not determinism; GPU kernels are nondeterministic."** **Remediation:** the stochasticity protocol (k=3, variance components as random effects) is itself the scientific answer; engineering answer: deterministic torch flags recorded in manifests, tolerance policy in `docs/reproducibility-guide.md` stating which artifacts must be byte-identical (splits, attributions from frozen models on CPU, all statistics, all figures) vs tolerance-bounded (GPU DeepSHAP, LLM outputs), and released frozen model weights so training never needs repeating.

**A3. "You cannot redistribute CICIDS2017/UNSW-NB15; your `data/` is a stub for me."** **Remediation:** the correction pipeline is deterministic and tested; `data-integrity.yml` verifies download checksums → corrected checksums → processed checksums; row-level split indices are in git; `REPRODUCING.md` gives per-dataset acquisition steps. Reviewer can verify the full chain from public sources without us redistributing anything.

**A4. "The circularity firewall is a promise."** **Remediation (adopted):** structural — separate packages, import-linter contracts, prompt-hash disjointness, schema-enforced model-family disjointness, `firewall-audit.yml`, and `docs/firewall.md` mapping each of the four firewall rules in the master plan to its enforcing mechanism (rule 1 → analysis configs for H3 headline enumerate only verifier-independent metric columns, schema-checked; rule 2 → this audit; rule 3 → coverage-risk analysis is a mandatory output of every B4 cell; rule 4 → verifier threshold appears only in dev-split-scoped configs, checked by schema).

**A5. "Pre-registered thresholds could have been back-dated in git."** Git dates are forgeable. **Remediation:** the OSF preregistration (external timestamp + DOI) contains the hash of the `configs/statistics/` tree at `prereg-v1`; the repo stores the OSF DOI; the two cross-attest. CI freeze prevents drift thereafter.

**A6. "Your `runs/` immutability is a convention on a filesystem."** **Remediation:** manifests + output hashes committed to git (payloads in DVC) — any tamper breaks hash verification in `manifest-audit.yml`; the release snapshot is an immutable Zenodo deposit; `tools/audit_manifests.py` maintains an append-only audit log of verification passes.

**A7. "Analysis selects runs; selection is where p-hacking lives."** **Remediation (adopted):** enumerated run IDs, no globs; hypothesis families and correction structure pre-registered; every deviation an append-only amendment; `mapping-completeness.yml` guarantees no paper number exists outside this chain. Residual risk: file-drawer of runs never cited — mitigated by `REGISTRY.md` being append-only and the paper's appendix auto-listing *all* registered experiments with status (generated table, so it cannot omit).

**A8. "Human-study reproducibility is impossible; de-identified data may still be withheld by IRB."** **Remediation:** preregistered analysis code + de-identified data release where permitted; `synthetic_sample/` lets anyone execute the exact analysis pipeline regardless; instruments, surface-matching build spec, and manipulation-check results released in full — the *instrument* is fully reproducible even where the *sample* is not re-collectable.

**A9. "The extractor audit set was annotated by authors — priming and circularity."** The plan already separates audit and plausibility annotation pools. **Remediation added:** annotation protocol, adjudication log, and per-item provenance released in `analysis/error_taxonomy/` style; disagreement (α) reported; audit-set item IDs stamped so no audit item leaks into headline metric sets.

**A10. "Windows-authored artifact, Linux execution — path/encoding drift."** **Remediation:** container digest in every manifest; CI runs on the container; path handling normalized (no absolute paths permitted in any config — schema regex forbids drive letters and leading `/`).

**A11. "Erasure imputation models are fitted — a hidden trained component."** **Remediation (adopted):** fitted imputation models are manifested cache artifacts with their own seeds, data hashes, and configs; Layer-2 numbers cite them as inputs; the ROAR secondary operator at the anchor bounds conclusions' sensitivity to the operator choice, per the plan.

**A12. "What if I find a bug in a metric after Tier A ran?"** The honest scenario most artifacts hide. **Remediation:** metrics carry formula versions; a fix = new formula version + new runs + a superseding registry entry + a CHANGELOG entry; old runs remain, labeled. The paper cites only current-version runs; the trail of the correction is public. This is what "no silent regeneration" means in practice.

**Verdict after remediations:** the artifact answers every standard rejection vector with a mechanical control rather than a promise; residual irreproducibility (API model drift, human-sample uniqueness, GPU tolerance) is *disclosed and bounded* rather than hidden — which is the standard exemplary ACM/NeurIPS artifacts actually meet.

---

## 9. Reviewer Reproduction Tiers (published in `REPRODUCING.md`)

| Tier | What is reproduced | From | Needs | Time |
|---|---|---|---|---|
| L1 | Every figure & table in the paper | released `analysis/outputs/` | container, CPU | < 30 min |
| L2 | Every statistic | released `runs/` artifacts | container, CPU | hours |
| L3 | Every metric incl. Layer-1/2, from explanations | released caches + LLM ledger (replay mode) | container, CPU | hours |
| L4 | Everything from raw data | public datasets + open weights + API access | GPU, API keys | days |

CI continuously exercises L1 and an L3 smoke slice; the artifact evaluation submission targets L1–L3.
