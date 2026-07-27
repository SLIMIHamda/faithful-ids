# Amendment 0003 — the estimand and the removal operator are reported parameters

- **Date:** 2026-07-27
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made **before**
  any Tier-A data exists. It formalises a methodological critique raised in
  review on 2026-07-25 and answered in code at commit `7696a85` (sufficiency
  co-reporting, switchable removal semantics, redundancy diagnostic)
- **Deciders:** project author (ruling)
- **Related:** [`../hypothesis_families.yaml`](../hypothesis_families.yaml)
  (frozen H1/H2/H3 — all three are stated against ε and φ),
  [`../../metrics/layer2_erasure.yaml`](../../metrics/layer2_erasure.yaml)
  (registered operators, k values),
  [`../../attribution/treeshap.yaml`](../../attribution/treeshap.yaml) (φ and its
  removal semantics),
  [`0002-h2-ablation-and-margin-headline.md`](0002-h2-ablation-and-margin-headline.md)
  (margin headline, mandatory per-class table),
  [`../../../analysis/configs/pilot_layer2_redundancy.yaml`](../../../analysis/configs/pilot_layer2_redundancy.yaml),
  `docs/adr/0001-layer2-eps-model-claim-driven.md`

## Why

Three objections apply to every erasure-based faithfulness number this project
reports, and none of them is answered by measuring more carefully:

1. **φ is a chosen reference, not ground truth.** TreeSHAP on the *predicted*
   class is one defensible attribution among several (different target class,
   different background policy, or a non-Shapley attributor family would each
   yield a different top-k). A generator that disagrees with φ is unfaithful
   *to φ*; calling that "unfaithful to the detector" overclaims.
2. **Correlation makes erasure protocol-dependent.** When a cited feature has a
   correlated neighbour, a conditional imputation operator restores much of the
   erased feature's signal from that neighbour, so the detector's score barely
   moves. The resulting near-zero comprehensiveness is a property of the
   *removal operator*, not evidence that the cited feature was irrelevant.
3. **Comprehensiveness alone cannot tell redundancy from irrelevance.** Both
   produce a low comprehensiveness. The distinction is only recoverable when
   sufficiency is read beside it.

The frozen prereg states H1/H2/H3 in terms of ε and φ but never says, in one
place, *what quantity those hypotheses estimate* or *which knobs the estimate is
conditional on*. This amendment says it, and makes the conditioning knobs
reported parameters rather than implementation details.

## (A) The estimand, stated

Every faithfulness number this project reports estimates

> **F(T ; φ, f, D, R, k)** — the agreement between an explanation text *T* and
> the **reference attribution φ**, measured on the **frozen detector f** over the
> **dataset/sampling design D**, under the **removal operator R**, at **cited-set
> size k**.

It is **not** an estimate of "the true reasons for *f*'s decision". No claim in
this project asserts access to the detector's true reasons; the reference is φ,
and φ is disclosed.

Consequences, binding on every reported number:

- **Layer-1** (`mention_precision`, `mention_recall`, `dsa_asserted` with
  `direction_assertion_rate`, `arc`) estimates agreement of *T* with **φ's
  top-k**. It is reference-relative and carries **no causal claim** about *f*.
- **Layer-2** estimates a **causal-under-R** quantity on *f*: `eps_att` scores
  φ↔*f* (claim-free, generator-blind), `eps_model` scores claims↔*f*
  (per explanation, ADR-0001). Both are defined **only relative to R**.
- **(φ, f, D, R, k) accompany the number.** No Layer-2 value appears in a paper
  table, figure, or analysis output without its operator named, alongside the
  per-class breakdown that amendment 0002 already made mandatory. `φ` and `f`
  are already pinned by the run manifest; `R` is added to `resolved_config` as
  `layer2_erasure_operator`.
- **Wording discipline.** "Faithful to the reference attribution", not
  "faithful to the detector"; "load-bearing under R", not "the feature the
  detector used". The `configs/attribution/treeshap.yaml` note calling φ the
  "GROUND-TRUTH attribution" is corrected to "reference attribution" by this
  amendment — the phrase was exactly the overclaim objection 1 names.

## (B) R is a reported parameter, and a sensitivity operator is registered

The frozen design registered a **primary** operator
(`conditional_expectation_imputation`, per-class kNN) and a **secondary** one
(`retrain_roar`, anchor scope only). Between them sits a cheap, blunt operator
that the design needed and did not have: fixed per-feature **training means**,
which severs the neighbour pathway that objection 2 exploits.

- **Registered as `sensitivity`:** `background_mean_imputation`, scope
  `invariance_check`. It is a **sensitivity analysis, never a headline** — no
  hypothesis is discharged on it.
- **Selection is a run parameter,** not a code edit: `run_pilot(erasure_operator=)`
  ∈ {`conditional` (default), `background`}, env
  `FAITHFULIDS_ERASURE_OPERATOR`, forwarded by `tools/rescore_run.py`, recorded
  in `resolved_config`.
- **The invariance check is a required companion to the Layer-2 headline.**
  Re-score the same claims under `background` (token-free replay — no
  generation, no GPU beyond the detector re-fit) and report whether the
  **generator ranking on ε_model moves**. Ranking-invariant ⇒ the Layer-2
  conclusion is not an artifact of the imputer's gentleness. Ranking moves ⇒
  that is a **finding and must be reported as one**, not resolved by picking the
  operator that agrees with the headline. The operator pair is fixed here,
  before the check has been run, so the choice cannot follow the result.
- **Magnitudes are not comparable across operators.** Only orderings are.

`retrain_roar` remains the anchor-only secondary and remains **unimplemented**
(`roar.py` is a deliberate fail-loud stub). Retraining is the only operator that
actually removes the substitute pathway rather than bounding it; until it runs at
the anchor, the redundancy verdict in (C) is bounded, not eliminated.

## (C) Sufficiency is co-reported; the 2×2 diagnostic is mandatory

Both quantities were always computed; only comprehensiveness was ever read. As
of this amendment **neither is reported alone.** Conventions, as implemented in
`faithfulids.metrics.layer2.metrics`:

- `comprehensiveness = s_full − s_erased` — **high is good**
- `sufficiency = s_full − s_kept` — **low is good**

They fail in **opposite directions** under correlation, which is what makes the
pair identify objection 2's case:

| | sufficiency LOW | sufficiency HIGH |
|---|---|---|
| **comprehensiveness LOW** | **redundant** — a correlated substitute carries the signal | **irrelevant** — the cited set carries nothing |
| **comprehensiveness HIGH** | **load-bearing** — necessary *and* sufficient | **necessary, not sufficient** |

The four-cell classification at the registered `k` and threshold is a
**mandatory reported companion** to any aggregate or per-class Layer-2 table,
implemented as the `layer2_redundancy` analysis test so it is produced by the
pipeline rather than by hand.

This already changed a stated conclusion. On the B1ℓ rerun (prob, k=3,
threshold 0.10, n=60): **37 redundant / 11 load-bearing / 7 necessary-not-sufficient
/ 5 irrelevant**, with **all 8 BENIGN and all 8 DDoS instances redundant**. The
prob-space ≈0.000 on the easy classes is therefore **redundancy, not attribution
failure** — superseding the earlier "saturation" wording, and independently
confirming amendment 0002's ruling that margin is the headline space.

## (D) What this amendment does not settle

Registered here so the limits are on the record, not discovered in review:

- **ROAR at the anchor** is the decisive test for the 37 redundant instances and
  has not been run (stub, registered, anchor-only).
- **Correlation stratification** — reporting the redundancy verdict against each
  cited feature's maximum correlation with a retained feature — requires the
  feature matrix and has not been computed.
- **A second attributor family** (permutation-based, *not* another SHAP variant —
  TreeSHAP here is already `exact=True`) is the test of objection 1. Not run.
- **A semi-synthetic ground-truth recovery test** — data with a known generating
  mechanism, checking that the pipeline recovers it — is the decisive answer to
  objection 1 and the most expensive. Not run.

None of these is a precondition for Tier-A. Each is a named limitation the
discussion section must carry until it is discharged.

## Implementation

Landed with this amendment: the `sensitivity` operator entry in
`configs/metrics/layer2_erasure.yaml` (+ schema support in
`configs/schema/metric.v1.json`), the φ wording correction in
`configs/attribution/treeshap.yaml`, the `layer2_redundancy` analysis test and
its `pilot_layer2_redundancy` config, and tests pinning (i) that
`resolved_config` records `layer2_erasure_operator`, (ii) that the operator
names accepted by the runner are exactly those registered in the metric config,
and (iii) the 2×2 classification boundaries. The switchable operator, the
sufficiency computation, and the launcher's token-free invariance cell landed
earlier at commit `7696a85`; the invariance cell has not yet been executed.
