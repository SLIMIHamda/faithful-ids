# Amendment 0011 — the verifier's verdict is read from its verdict line

- **Date:** 2026-10-04
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** [`0008-verifier-pinned-h3-joins-tier-a.md`](0008-verifier-pinned-h3-joins-tier-a.md)
  (A.5) and [`0010-verifier-phi4-14b.md`](0010-verifier-phi4-14b.md) ("same verdict
  rule"), on the prereg frozen at tag `prereg-v1`
- **Timestamp of record:** the git commit introducing this file — made after the
  amendment 0010 re-check and **before** any Tier-A run is scored
- **Deciders:** project author (ruling)
- **Related:** `src/faithfulids/generation/b4_vte/verifier/verifier.py`
  (`read_verdict`), [`../../../experiments/verifier_recheck/amendment_0010/README.md`](../../../experiments/verifier_recheck/amendment_0010/README.md)

## Why

The verifier prompt (`b4_vte/verifier` 1.0.0, frozen) ends: "output a single
verdict token on its own line — `SUPPORTED` … `UNSUPPORTED` otherwise". The code
did not read that line. It searched the whole reply: supported only if the word
`SUPPORTED` appears and the word `UNSUPPORTED` appears nowhere.

The prompt's own check 3 reads "Are there unsupported or invented magnitude
claims?". A model that restates the checks before answering always has the word
in its reply. Phi-4 (14B) does exactly that. In the amendment 0010 re-check,
all 38 of its replies end with the line `SUPPORTED`, after correct answers to
the three checks, and the first reader called all 38 unsupported.

## (A) The change

The verdict is the **last line that holds only the verdict token**, after
stripping markdown, code fences, quotes and an optional "Verdict:" label. A reply
with no such line is still not supported (fail-safe, as in amendment 0008(A.5):
the instance abstains and shows its B1 fallback). The prompt, the models and the
abstention rule do not change.

## (B) Effect on the record

- Phi-4-mini (smoke run, 2026-10-03): unchanged. All 38 replies have the verdict
  line `UNSUPPORTED`. Amendment 0010's diagnosis stands.
- Phi-4 (14B), the re-check of 2026-10-04: re-read from the recorded replies
  (ledger replay, no new model call): 38 `SUPPORTED`, 0 rejections.
- Amendment 0010(B) is applied to these re-read verdicts: with 0 rejections,
  none is wrong, and **Phi-4 is the verifier for every Tier-A run**. The record
  is `experiments/verifier_recheck/amendment_0010/`.
- No Tier-A run has been scored, so no result changes.

## (C) Session plan (no scientific change)

Phi-4 writes ~317 tokens per verdict, ~28 s on a T4: ~6 h for the 800 B4/B5
drafts of one generator model at N=400. That does not fit one 12 h score session
beside extraction and judging. The verifier pass therefore gets its own
resumable Kaggle step (`PHASE='verify'`), between generate and score. The score
step reads every verdict from that step's ledger. Same calls, same results.
