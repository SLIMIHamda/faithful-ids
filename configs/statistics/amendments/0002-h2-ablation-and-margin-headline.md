# Amendment 0002 — H2 as a freedom/access ablation; margin the headline Layer-2 space

- **Date:** 2026-07-25
- **Status:** Registered (append-only; never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made before any
  Tier-A data exists; the diagnostic that motivated it is the K-way contingency
  smoke `EXP-PILOT-001__3d9e4cb__2026-07-24T1650Z` (N=60, non-citable)
- **Deciders:** project author (ruling), post-smoke design review
- **Related:** [`hypothesis_families.yaml`](../hypothesis_families.yaml) (frozen H2/H3),
  [`../../generators/b3_dte_style.yaml`](../../generators/b3_dte_style.yaml) (b3 → grounded-natural, prompt 1.2.0),
  [`../../generators/b1l_llm_render.yaml`](../../generators/b1l_llm_render.yaml) (B1ℓ ceiling),
  [`../../../experiments/tier_a/EXP-A-005_instrument_ceiling.yaml`](../../../experiments/tier_a/EXP-A-005_instrument_ceiling.yaml),
  `docs/adr/0001-layer2-eps-model-claim-driven.md`

## Why

The contingency smoke exposed two measurement faults that the frozen prereg would
otherwise have carried into the ~43-GPU-h Tier-A wave 1:

1. **b3's K-way prompt was a transcription task.** "Proceed down the list,
   reference only the factors provided" pinned mention precision, recall, rank
   correlation, and direction agreement at 1.000 by construction (verified: b3 =
   1.000/1.000/0.998 across 60 instances). As frozen, H2 tests "faithfulness
   drops as narration becomes more free-form" via **B2 vs B3** — but that
   comparison confounds *narrative freedom* with *attribution access* (B2 sees no
   attribution; B3 sees and recites it). Two dimensions moved at once, and one
   arm was a definitional ceiling.

2. **Aggregate Layer-2 in probability space is uninformative on a confident
   detector.** Per predicted class, prob-space comprehensiveness@3 was exactly
   0.000 on BENIGN, DDoS, and PortScan (the detector sits at p≈1.0; erasing three
   features moves it not at all) and only un-saturated on Bot/SSH-Patator/DoS.
   The 0.270 aggregate was an average over a bimodal distribution, and the class
   that carried the most prob-space signal (Bot, 0.758) is the one the
   class-handling contingency (amendment 0001) excludes.

## (A) H2 is redefined as a two-arm ablation, attribution access held constant

The frozen `hypothesis_families.yaml` text for **H2** and its members
(`h2_layer1_f1_drop`, `h2_dsa_asserted_drop`) stand as the registration record.
Their operationalization is amended:

- **Arm a — B1ℓ** (`b1l_llm_render`): an LLM given the ranked attribution and
  asked to recite it (the former b3 1.1.0 transcription prompt). Maximal
  constraint; a rendering ceiling.
- **Arm b — B3-natural** (`b3_dte_style` prompt 1.2.0): an LLM given the *same*
  attribution and KB evidence and asked to explain in its own words (b4's drafting
  prompt with verification disabled). Maximal narrative freedom at equal access.

Both arms see byte-identical evidence (same top-5 ranked list, same KB snippets;
enforced by a parity test), so **a→b isolates narrative freedom with attribution
access held constant** — the clean test of H2. B2 (no attribution) is retained as
a baseline but is no longer the H2 comparator, because it varies access too.

**Headline Layer-1 metric for H2 is demoted from `mention_f1` to precision and
recall reported separately, plus a coverage–risk curve.** `mention_f1` penalizes
principled pruning: a generator that drops unverifiable claims loses recall (and
F1) at unchanged precision, which reads as "less faithful" when it is more
disciplined. In the smoke, B4/B5 precision was 0.988/0.992 at recall 0.657/0.577
— a precision-for-coverage trade the single F1 number hides. P/R split +
coverage–risk is the correct headline regardless of the B3 fix.

## (B) Margin is the pre-registered headline Layer-2 space; prob is a finding

- **Confirmatory Layer-2 (H3) is computed in `margin` space**, per-feature
  ε_model (`component: eps_model`, the claim-driven per-generator quantity that
  H3 already designates), reported at **k ∈ {1, 3, 5}** with the per-feature
  normalization (`comprehensiveness_cited_per_feature` / `sufficiency_cited_per_feature`)
  as the headline because it removes cited-set-size dependence. Probability space
  stays emitted (`delta_spaces: [prob, margin]`, unchanged) but is **reported as a
  finding, not a co-headline**: erasure in probability space is unreliable when
  the detector is near-certain, a caution the ERASER-lineage literature has not
  had to internalize because its tasks are not saturated. This is a stated
  methodological result, not a defect.
- **Per-class Layer-2 is a mandatory reported breakdown.** No aggregate Layer-2
  number appears in the paper or an analysis output without its per-class table
  beside it. The aggregate misled twice in one run; the breakdown is the datum.

## (C) The 7-class figure requires a re-fit, and this run does not preview it

Recorded so nobody slides past it: resolving the contingency (excluding Bot)
changes the detector, which changes the attributions, which changes every
downstream number. The smoke is a diagnostic of the machinery, not a preview of
the 7-class result — none of its values carry over.

## Sequencing note (for the methods section)

The prereg was frozen (`prereg-v1`) before a design shakedown, and the first
smoke immediately found a broken baseline — hence amendments 0001 and 0002 land
before any Tier-A data. The ordering that would have avoided them is
**G-001 → shakedown smoke → freeze**: run the extractor-audit gate and a
throwaway end-to-end smoke to shake out instrument and baseline faults, *then*
freeze. This is not actionable retroactively (the freeze and its amendments are
the honest record), but it is the sentence the methods section should carry when
it explains what the amendments are and why pre-data amendments exist.

## Implementation

The generator/prompt/roster changes are direct edits (prompts and generator
configs are not in the frozen trio); this amendment governs the frozen H2/H3
operationalization. The analysis layer implements the P/R + coverage–risk
headline and the mandatory per-class Layer-2 breakdown.
