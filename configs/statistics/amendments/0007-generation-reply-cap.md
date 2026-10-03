# Amendment 0007 — generation reply cap: declared, 1024 tokens, part of the call key

- **Date:** 2026-10-03
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made **before**
  any Tier-A generation at N=400 and before any 7-class run is scored
- **Deciders:** project author (ruling), on the Tier-A smoke run of 2026-10-03
- **Related:** `configs/generators/{b1l_llm_render,b2_zeroshot,b3_dte_style,b4_vte,b5_narrative_vte}.yaml`,
  [`0002-h2-ablation-and-margin-headline.md`](0002-h2-ablation-and-margin-headline.md)
  (the H2 ablation whose pilot numbers this affects)

## Why

No configuration ever set how long a generated explanation may be. The
transformers provider stopped every reply at a default of **160 new tokens**,
and the generators never overrode it. The B3–B5 prompts ask for a per-feature
explanation of five features with feature meanings, which does not fit in 160
tokens. The replies stop mid-sentence:

| generator | K-way pilot `5377b81` (Qwen3-8B) | Tier-A smoke `2968aab` (Qwen3-8B, N=20) |
|---|---|---|
| B2 (no SHAP, "3–5 sentences") | 1 / 59 cut off | 0 / 20 |
| B3 (grounded, free text) | 68 / 118 | 19 / 19 |
| B4 (verify-then-explain draft) | 59 / 59 | 19 / 19 |
| B5 (narrative) | 59 / 59 | 19 / 19 |

A feature the text was about to mention when the cap hit is a claim that never
reaches the extractor. That lowers Layer-1 recall for exactly the generators
H2 and H3 compare, and the drop measures the cap, not faithfulness.

## (A) The change

- Every LLM generator config declares `params.max_new_tokens: 1024`. Generation
  still stops at end-of-text, so the cap costs time only on replies that really
  are that long.
- The generators send it with each call. It is therefore part of the ledger's
  request hash: a reply made under one cap is never served for a request under
  another.
- The provider applies the cap it is sent; 160 remains only as the fallback for
  a call that declares none.
- Prompts, models, temperature (0), seeds and every other generation input are
  unchanged.

## (B) Consequences for earlier numbers

- Every pilot number involving B3, B4 or B5 was measured on cut-off text. That
  includes the H2 pilot result (B3 recall 1.00 → 0.70) and the H3 pilot result
  (verifier adds nothing to precision). They were non-citable already. They are
  now also **known to be confounded** and are not to be quoted as evidence,
  even informally, without this caveat.
- Old pilot ledgers do not replay under the current generator configs (their
  calls carry no cap, so the request hashes differ). They are superseded anyway
  by the 7-class taxonomy (amendment 0001, applied 2026-10-03).

## (C) Required reporting

Every run reports `reply_cap_hit_rate` (layer `cost`): the share of its
generation calls whose reply reached the cap. It is expected to be near 0. A
non-trivial rate is reported beside the generator results it affects, never
dropped.
