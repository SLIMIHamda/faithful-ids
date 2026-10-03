# Amendment 0005 — the extractor's 4-bit weights: Google's QAT GGUF, served by Ollama

- **Date:** 2026-10-03
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made **before**
  the registered (LLM-assisted) extractor has produced a single claim, so no
  result could have shaped it
- **Deciders:** project author (ruling)
- **Related:** [`../../extraction/eval_extractor.yaml`](../../extraction/eval_extractor.yaml)
  (the instrument, now version 2.2.0),
  [`0004-directional-evidence-rule.md`](0004-directional-evidence-rule.md)
  (the rule the gate scores under, unchanged), `experiments/gates/EXP-G-001_extractor_audit.yaml`,
  `kaggle/extractor_regate/`

## Why

The registered extractor is `google/gemma-4-26B-A4B-it` at 4 bit. The config
loaded it with transformers + bitsandbytes nf4. That load cannot work on any
hardware this project has:

- Gemma 4 is a mixture-of-experts model. 128 experts × 30 layers hold 22.8B of
  its 25.2B parameters (~91%).
- transformers stores those experts as fused 3D parameters, not `nn.Linear`
  layers. bitsandbytes only quantises `nn.Linear`. So "4-bit" leaves ~91% of
  the weights in fp16, about **48 GB**.
- Kaggle offers 2 × 16 GB (T4). The incoming RTX 5090 has 32 GB.

This explains the 2026-08-23 Kaggle crash (modules spilled to CPU, which
bitsandbytes refuses). The GPU-count check added after it would not have
prevented a repeat: the size estimate behind it (~14 GB) assumed every layer
gets quantised.

## (A) The change

Same model, same family, same prompt, same temperature (0), same rule engine.
Only the 4-bit weights and the program serving them change:

| | before | after |
|---|---|---|
| weights | `google/gemma-4-26B-A4B-it` @ `5305c1e`, nf4 at load time | `google/gemma-4-26B-A4B-it-qat-q4_0-gguf` @ `d1c082b`, file `gemma-4-26B_q4_0-it.gguf` |
| size | ~48 GB as actually loaded | 14.4 GB |
| file pin | none (`sha256: null`) | sha256 `3eca3b8f…a51d` |
| runtime | transformers | Ollama ≥ 0.30.5, Gemma 4 chat renderer, thinking off |
| reply cap | 160 new tokens (generator default) | 1024 new tokens |

The new weights are Google's own quantisation-aware-trained (QAT) Q4_0 release.
Google trained them to stay close to bf16 quality at 4 bit. They are arguably
closer to the full model than post-hoc nf4 would have been.

Ollama's library ships its own copy of this file (`gemma4:26b-a4b-it-qat`). It
differs from Google's by 2,144 bytes, so it is **not** used. The run loads
Google's file and checks its sha256. The provider then refuses to run unless
the model Ollama serves is stored under that same sha256.

**Reply cap.** One extracted claim is ~25–30 tokens of JSON. 117 of the 300
audit texts carry 5 or more claims, so a 160-token cap would cut the JSON short.
The reply would fail to parse and that item would silently fall back to the rule
engine. 1024 tokens removes that failure mode.

## (B) What does not change

- The gate: EXP-G-001, extractor F1 ≥ 0.95 under amendment 0004's rule, on the
  same 300 items and the same gold.
- The prompt asset (`eval_extractor` 1.0.0, same sha256).
- The firewall: the extractor is still `gemma`, disjoint from every generator
  family and from the verifier family.

## (C) Required reporting

Every result from the LLM-assisted extractor reports, together:

1. instrument version 2.2.0 and the GGUF sha256 above;
2. the Ollama version that served it;
3. how many items fell back to the rule engine, because the model's reply did
   not parse. A run where every item fell back scores the rule engine, not this
   instrument, and does not count as an attempt at the gate.

## (D) Attempt log

Attempts 1–4 (extractor 1.5.0–2.1.0) all scored the rule-only fallback; see
amendment 0004(D). The next attempt is the first to score the registered
instrument. It is recorded here only by reference: its result lives in
`experiments/gates/EXP-G-001_audit_v2/gate_result.json` and the commit that adds it.
