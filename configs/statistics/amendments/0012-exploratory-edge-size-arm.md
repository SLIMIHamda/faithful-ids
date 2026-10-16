# Amendment 0012 — an exploratory edge-size arm: Qwen3-1.7B (EXP-A-006)

- **Date:** 2026-10-13
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** nothing in the confirmatory plan. It adds one exploratory experiment
  next to the prereg frozen at tag `prereg-v1`
- **Timestamp of record:** the git commit introducing this file — made **after**
  the EXP-A-001 runs of Qwen3-8B and Qwen3-4B were scored and **before** any
  Qwen3-1.7B generation call
- **Deciders:** project author (ruling)
- **Related:** [`../../../experiments/tier_a/EXP-A-006_edge_size_qwen3_1_7b.yaml`](../../../experiments/tier_a/EXP-A-006_edge_size_qwen3_1_7b.yaml),
  [`../../llms/qwen3_1_7b_4bit.yaml`](../../llms/qwen3_1_7b_4bit.yaml)

## Why

The first two EXP-A-001 runs (commit `eda21a4`; descriptive numbers, not the
registered tests):

- **Qwen3-8B** (run `EXP-A-001__eda21a4__2026-10-12T0217Z`): B3, B4 and B5 are at
  ceiling. Mention F1 0.997–1.000, asserted-direction accuracy 1.000, and they
  state a direction for 95–100% of the features they cite. The verifier rejected
  no draft.
- **Qwen3-4B** (run `EXP-A-001__eda21a4__2026-10-13T0427Z`): mention F1 and
  asserted-direction accuracy stay at ceiling, but the free-text generators often
  state no direction. B3 states one for 62% of cited features and B5 for 29%.
  144 of 396 B3 explanations and 195 of 396 B5 explanations state none at all.
  The verifier rejected 3 of 684 drafts.

So the room for the generators and the verifier to differ opens below 8B. The
authors also want to know what a model small enough to run on the machine that
hosts the IDS would do. Qwen3-1.7B is the next size down in the same family.

Because this arm was chosen after seeing those results, it is **exploratory**.

## (A) The arm

EXP-A-006 is EXP-A-001's protocol with one change, the generator LLM:
`qwen3_1_7b_4bit` (Qwen/Qwen3-1.7B at HF commit `70d244cc`, the same 2025-07-26
snapshot date as the 4B and 8B pins, 4-bit nf4). Everything else is the same:
the data, the K-way detector, the N=400 sample and seeds, generators B0–B5, the
extractor (2.3.0, amendment 0005), the B4/B5 verifier (Phi-4, amendments 0008,
0010, 0011), the plausibility judge (Command R7B, amendment 0009), Ollama 0.35.1,
and the EXP-G-001 and EXP-G-002 gates in every score session.

## (B) What is reported, fixed now

For each generator, beside the same numbers for the 4B and 8B arms (same
instances): mention precision, recall and F1; `dsa_asserted` averaged over
explanations that assert at least one direction; `direction_assertion_rate`; the
share of explanations that assert no direction; ARC; HFR; Layer-2 cited
comprehensiveness and sufficiency (k = 1, 3, 5; probability and margin); the B4/B5
verifier rejection rate and coverage; and the plausibility ratings (from an
unvalidated judge, labelled so). Each is a descriptive estimate with a 95%
bootstrap interval over instances. **There are no hypothesis tests.** Nothing from
this arm enters H1, H2 or H3, their Holm families or any headline claim. The paper
reports it in its own exploratory section.

## (C) Deployment measurements

For each generator model the paper reports what the generate sessions already
record: the GPU memory taken by the model's weights at load (logged by the
provider) and the per-call latency and token counts from the generation ledger.
These are Kaggle T4 numbers (bitsandbytes 4-bit), not edge-hardware numbers. A
benchmark on other hardware would need its own registration.

## (D) What does not change

EXP-A-001, its four-model roster, H1–H3, their member tests and their thresholds.
`direction_assertion_rate` stays a co-reported metric of H2 and H3, as registered.
It does not become a test.

## Order of runs

The 1.7B arm runs next (generate, verify, score), before EXP-A-001's Mistral-7B
and Qwen3-32B arms. This is a scheduling choice only.
