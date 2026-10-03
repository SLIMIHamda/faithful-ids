# Amendment 0008 — the B4/B5 verifier gets a pinned model; H3 joins EXP-A-001

- **Date:** 2026-10-03
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made **before**
  the phi verifier has judged a single draft and before any Tier-A run is scored
- **Deciders:** project author (ruling)
- **Related:** [`../../generators/b4_vte.yaml`](../../generators/b4_vte.yaml),
  [`../../generators/b5_narrative_vte.yaml`](../../generators/b5_narrative_vte.yaml),
  `experiments/tier_a/EXP-A-001_core_factorial.yaml`,
  [`0007-generation-reply-cap.md`](0007-generation-reply-cap.md) (why the pilot's
  H3 numbers say nothing), [`0009-plausibility-judge-pinned-and-validated.md`](0009-plausibility-judge-pinned-and-validated.md)

## Why

H3 asks whether Verify-then-Explain (B4) makes explanations more faithful than
the same draft without the check (B3). Three things stood in the way:

1. **The registered verifier had no model.** B4 and B5 name a `phi`-family
   verifier, but no checkpoint was ever pinned. Every pilot and smoke run used
   a model-free rule checker instead.
2. **The rule checker tests what Layer 1 scores.** It approves a draft when the
   cited features are in the evidence and their stated directions match the
   attribution signs. Layer 1 scores the same two things. A Layer-1 gain of B4
   over B3 under that checker is partly built in, and the prereg asks for H3 on
   verifier-*independent* signals.
3. **No experiment listed H3.** `hypothesis_families.yaml` defines H3, but
   EXP-A-001 registered only H1 and H2, so H3 had no confirmatory home.

## (A) The change

**1. Pinned verifier model.** Microsoft publishes Phi-4-mini only in full
precision. The verifier runs Ollama's 4-bit library build of the official
weights, pinned by its blob digests:

| | value |
|---|---|
| base model | `microsoft/Phi-4-mini-instruct` (3.8B, MIT licence) |
| build | Ollama library `phi4-mini:3.8b-q4_K_M` (Q4_K_M, 2.49 GB) |
| weights blob | sha256 `3c168af1…a5db` |
| chat template blob | sha256 `813f53fd…a603` |
| runtime | Ollama ≥ 0.30.5, temperature 0, seed = run seed, no thinking field |

A library tag can be re-pointed; a digest cannot. The score step checks every
blob in the pulled manifest against these pins, and the provider refuses to
call a model whose weights or chat template differ.

**2. When it runs.** B4 and B5 make exactly one generation call per instance.
The verifier then reads that draft, and its verdict only decides whether the
draft is shown or replaced by the B1 template. Verifying after generation is
therefore the same instrument. The verifier runs in the Tier-A **score** step,
on the draft replayed from the generation ledger, beside the extractor. Its
calls get their own ledger, so a re-score replays them. The generation
ledgers do not depend on the verifier and stay valid. B4 and B5 share this one
verifier, as registered.

**3. H3 joins EXP-A-001.** Its `hypothesis_family` becomes `[H1, H2, H3]`, with
the members `hypothesis_families.yaml` already defines (`h3_layer1_gain`,
`h3_layer2_gain`), on B3 vs B4 across the four generator models. Tier-A scoring
now refuses the rule checker.

**4. The threshold sweep is void.** `verifier_threshold` (0.3 / 0.5 / 0.7,
dev-split tuned) assumes the verifier outputs a score. The registered verifier
prompt (`b4_vte/verifier` 1.0.0, unchanged) outputs a verdict token,
`SUPPORTED` or `UNSUPPORTED`. There is nothing to cut at three levels and
nothing to tune on a dev split. The frozen `decision_thresholds.yaml` is left as
it is; this amendment records that the key is unused.

**5. Replies with no verdict token** count as unsupported (fail-safe, as the
registered code already does): the instance abstains and shows its B1
fallback.

## (B) What does not change

- The verifier prompt (1.0.0, same sha256) and the B4/B5 generator prompts.
- The firewall: `phi` stays disjoint from every generator family (qwen,
  mistral, llama3, frontier), from the extractor (`gemma`) and from the judge
  (`command_r`).
- The abstention rule: unsupported → show B1, never silence.
- The generation ledgers and the reply cap (amendment 0007).

## (C) Required reporting

Every Tier-A run reports, together:

1. the verifier build and weights sha256, and the Ollama version that served it;
2. `verifier_no_verdict_rate`: replies with no verdict token;
3. B4's and B5's abstention rate (coverage) per generator model.

An abstention shows the B1 template, which is faithful by construction, so
abstention alone raises B4's faithfulness. Every H3 result is therefore
reported beside B4's coverage, and also on the drafts the verifier accepted.
The H3 analysis config is committed before any H3 test is computed.
