# ADR-0001 — Layer-2 measures ε_model (claim-driven); attribution-driven erasure is ε_att

- **Status:** Accepted (2026-07-07)
- **Deciders:** project author (ruling), pilot-v1 post-mortem review
- **Supersedes:** the implicit "Layer-2 is model-level, claim-free, once per instance" design
- **Related:** Pass B (extractor audit), pilot-v2 plan; `framework/decomposition.py`,
  `framework/interfaces.py`, `metrics/layer2/`

## Context

The pilot-v1 run (`EXP-PILOT-001__371f2d8`) emitted 240 Layer-2 rows keyed on
`instance_id` only, computed from the SHAP attribution's top-k features, once per
instance. Investigating why comprehensiveness was ≈ 0 for 118/120 rows surfaced a
**contradiction inside the L0 spine** — the two formal modules disagree on what
Layer-2 is supposed to measure:

| Source | Layer-2 target | Feature set erased |
|---|---|---|
| `framework/decomposition.py` (§3-in-code) | **ε_model** = gap between the *explanation's claims* and the model; "probes directly, without routing through the attribution" | cited features **S** (claim-driven, per generator) |
| `framework/interfaces.py` (`Layer2Metric`) | claim-free: *"No generator identity, and no claims … independent of any narration"* | attribution top-k **φ** (claim-free) |
| `metrics/layer2/metrics.py` (impl) | followed `interfaces.py` | φ |

There is no written Proposition 1 to break the tie (`paper/manuscript/` is a
placeholder), and `REPOSITORY_BLUEPRINT.md` §5 is compatible with either reading
(it lists `claims` as a *general* metrics input but never pins Layer-2's erased
set). As implemented, Layer-2 measured **ε_att** (φ ↔ f), not ε_model — so the
framework's headline per-generator quantity was never computed.

## Decision

**Layer-2's primary measurement is ε_model, claim-driven.** `decomposition.py` is
authoritative (it is the paper's §3 in code); `interfaces.py`'s "no claims" clause
was an over-application of the generator-blindness invariant.

1. **Add** a claim-driven ε_model metric family — `comprehensiveness_cited` /
   `sufficiency_cited` — that erases the top-k **cited** features S (from the
   `ClaimSet`), computed per (instance, generator).
2. **Keep and relabel** the existing attribution-driven metrics
   (`comprehensiveness` / `sufficiency`) as the **ε_att** family: claim-free,
   generator-blind, once per instance. Their comparison with ε_model empirically
   probes ε_att beyond the a-priori `exact` flag (Proposition 1 bound check).
3. **Formula version** bumped to layer2 `1.1.0` (additive; ε_att metrics unchanged
   at metric-level `1.0.0`). Metric rows now carry a `component` field
   (`eps_att` / `eps_model`).
4. **v1's 240 Layer-2 rows are relabeled ε_att** in the post-mortem — not
   discarded. v1 is NON-CITABLE regardless.

### The invariant is preserved, not broken

The circularity firewall forbids passing **generator identity** into a metric —
not claim **content**. `Layer2ModelMetric` receives the `ClaimSet` (a legal input,
per blueprint §5) and never learns which generator authored it; `generator_id` is
attached downstream as an opaque grouping key, exactly as for Layer-1. Import
contract "Edge 1: metrics are generator-blind" remains KEPT.

## Consequences

- The comprehensiveness ≈ 0 finding is now separately diagnosable. Two live
  causes remain (probability saturation on a near-certain XGBoost; gentle
  conditional-expectation imputation choosing correlated proxies). Layer-2 metrics
  therefore gained an optional `delta_space` ∈ {`prob` (default), `margin`}; a
  margin accessor (`DetectorArtifact.predict_margin`, XGBoost `output_margin=True`,
  logit fallback) was added. **The emitted run stays `prob` until the saturation
  diagnostic is reviewed** — no semantic flip precedes evidence.
- An **erasure-efficacy CI smoke test** now guards the whole layer: erase-all must
  move the score materially, erase-none by 0. This would have caught v1's no-op
  before any LLM tokens were spent.
- Test `test_metric_rows_encode_generator_blindness` was updated: ε_att rows carry
  no `generator_id`; ε_model rows do.

## Out of scope (deferred, with reasons)

- **Extractor changes (Pass B).** Numeric-sign parsing (the B0 DSA artifact) and
  residual-span emission (claim-level hallucination) touch the audit-gated
  extractor (F1 ≥ 0.95, hash-registry prompts). They require an audit-set
  extension (v1's set lacked bare-numeric and free-form-fabrication cases), a gate
  re-run, and an extractor **semver bump** — one validation cycle, done together.
- **mention_F1 demotion.** To be recorded as a component metric (report P/R +
  claim-hallucination separately), with B0/B1 defined as faithful-by-construction
  reference ceilings excluded from the confirmatory B-vs-B Friedman. Prereg edit,
  pre-freeze, logged rationale.
### Landed with this pass (related Pass A items)

- **Imbalance-aware detector competence gate.** Runs are refused before any tokens
  unless the detector clears macro-F1 AND a per-attack-family detection-recall
  floor on the held-out explanation set (`configs/statistics/decision_thresholds.yaml`);
  the full per-family table → `competence.json` + the run manifest; exemptions are
  logged in the detector config. Faithfulness on an incompetent detector is noise.
- **Generation revisions pinned.** All open-weights LLM configs pinned to explicit
  HF commit hashes; `configs/schema/llm.v1.json` now rejects any non-commit
  `weights.revision`, making an unpinned generation revision structurally
  impossible. Pilot-v1's own revision is **unrecoverable** (it ran unpinned) — which
  is precisely the argument for the schema rule.
- **Saturation diagnostic** (`tools/layer2_saturation_diagnostic.py` +
  `faithfulids.metrics.layer2.saturation`) recomputes both Layer-2 families in prob
  and margin space over a run's re-derived inputs (read-only; new report). Its v1
  numbers are produced in the pinned env and paired with the Layer-2 diff at the
  review that precedes pilot-v2 generation.
