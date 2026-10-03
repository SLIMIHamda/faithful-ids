# Amendment 0009 — the plausibility judge gets a pinned model and a validation protocol

- **Date:** 2026-10-03
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made **before**
  the judge has rated a single explanation and before any human rating exists
- **Deciders:** project author (ruling)
- **Related:** [`../../metrics/plausibility_judge.yaml`](../../metrics/plausibility_judge.yaml),
  `prompts/judging/plausibility/v1.0.0.md`, `experiments/tier_a/EXP-A-001_core_factorial.yaml`,
  [`0008-verifier-pinned-h3-joins-tier-a.md`](0008-verifier-pinned-h3-joins-tier-a.md)

## Why

H1 — how convincing an explanation sounds does not tell you whether it is
faithful — is the paper's title claim. It needs a plausibility score for every
explanation. The prereg registers an LLM judge from the `command_r` family that
rates clarity, helpfulness and believability (1–5). The judge counts only if it
agrees with human ratings at Spearman ρ ≥ 0.6; below that it is dropped. But:

1. no judge model was ever pinned, so no run computed plausibility;
2. the validation names its statistic and threshold, but not which
   explanations are rated, by whom, or how the scores are combined.

## (A) The judge model

Cohere publishes Command R7B only in full precision. The judge runs Ollama's
4-bit library build of the official weights, pinned by its blob digests:

| | value |
|---|---|
| base model | `CohereLabs/c4ai-command-r7b-12-2024` (7B, CC-BY-NC 4.0 + Cohere acceptable-use addendum) |
| build | Ollama library `command-r7b:7b-12-2024-q4_K_M` (Q4_K_M, 5.06 GB) |
| weights blob | sha256 `b32d935e…b6f6` |
| chat template blob | sha256 `0d8282ca…d327` |
| params blob | sha256 `d8455b5d…4660` (Command R's turn stop tokens only) |
| runtime | Ollama ≥ 0.30.5, temperature 0, seed = run seed, no thinking field |

The 7B size is chosen so the judge fits beside the extractor and the verifier
in one score session (about 22 GB of 2 × 16 GB). The score step checks every
blob in the pulled manifest against these pins, and the provider refuses a
model whose weights or chat template differ.

**How it runs.** In the Tier-A score step, one independent call per explanation,
with the registered prompt (`plausibility` 1.0.0, unchanged). It rates the text
each generator finally shows: a B4/B5 abstention is rated as its B1 fallback.
The calls are shuffled with the run seed, as the registered harness specifies;
being independent, their order cannot change a score. The calls get their own
ledger, so a re-score replays them. A reply that does not parse gives no score
for that explanation and is counted (`judge_unparsed_rate`).

## (B) Validation protocol

**Items.** 120 explanations: 20 per generator (B0–B5). Drawn by a committed
script with a fixed seed, from the explanations of the four Tier-A score runs
(one per generator model), once all four exist. B2–B5 items are spread evenly
over the four models; within each generator the items are spread evenly over
length tertiles. The item list is committed before anyone reads the judge's
scores for those items.

**Raters.** Two people (the author and one co-author). Each rates every item
alone, with the judge's rubric and 1–5 scale, blind to the generator, the
model, the judge's scores and the other rater. Each sees the items in their own
random order.

**Statistic.** Per item, the human score is the mean over both raters and the
three dimensions; the judge score is the mean of its three dimensions. The
judge passes if Spearman ρ between the two, over the rated items, is **≥ 0.6**
(the registered threshold). Items the judge could not score are left out and
counted. Reported alongside, descriptively: ρ per dimension, and agreement
between the two raters (Krippendorff's α, ordinal).

**One attempt.** The first complete set of ratings decides. No re-rating, no
prompt change and no other model may be tried to rescue a failed judge.

**If it fails** (ρ < 0.6), the judge is dropped as registered. H1 is then tested
on the human ratings of the 120 items only, and reported as such.

## (C) Required reporting

- Every run with judge scores records `plausibility_judge.validated: false`, and
  lists the open validation under `instrument_gaps`. Judge scores may not enter
  any H1 result until a committed validation result with ρ ≥ 0.6 exists.
- The validation result (ρ, n, per-dimension ρ, rater agreement) is committed as
  its own record, with the item list and both raters' ratings.
- The judge's licence is non-commercial: its scores and the ratings are released
  with the paper's artifacts; the model weights are not redistributed.
