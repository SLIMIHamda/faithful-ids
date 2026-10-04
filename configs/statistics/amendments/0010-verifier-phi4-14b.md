# Amendment 0010 — the verifier model: Phi-4 (14B) replaces Phi-4-mini; one more attempt only

- **Date:** 2026-10-04
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** [`0008-verifier-pinned-h3-joins-tier-a.md`](0008-verifier-pinned-h3-joins-tier-a.md)
  (section A.1, the pinned model), on the prereg frozen at tag `prereg-v1`
- **Timestamp of record:** the git commit introducing this file — made after one
  N=20 smoke run of the verifier and **before** any Tier-A run is scored
- **Deciders:** project author (ruling)
- **Related:** [`../../generators/b4_vte.yaml`](../../generators/b4_vte.yaml),
  [`../../generators/b5_narrative_vte.yaml`](../../generators/b5_narrative_vte.yaml)

## Why

Amendment 0008 pinned Phi-4-mini (3.8B) as the B4/B5 verifier. Its first run was
the score-step smoke test of 2026-10-03 (Kaggle kernel `faithfulids-tier-a` v4,
commit `d02c8ab`, Qwen3-8B drafts, N=20). It rejected **all 40** B4/B5 drafts. Its
stated reasons are false on their face. For example:

- "Feature `Init_Win_bytes_backward` is mentioned in the draft but not in the
  evidence" — it is item 4 of the evidence list.
- "The direction for `Total Length of Fwd Packets` is incorrect; it should
  increase the PortScan score, not decrease it" — the draft says it "increases
  the PortScan score".
- "The direction for `Bwd Packet Length Mean` is incorrect; it should be an
  increase, not a decrease" — the draft calls it "elevated" and lists it among
  the features "contributing to increasing the DDoS score".

On the same drafts the extractor finds every cited feature in the evidence with
the right direction (Layer-1 mention F1 1.0 for B3, B4 and B5 drafts alike). A
verifier that rejects everything turns B4 and B5 into the B1 template, so H3
would compare B1 with B3 instead of testing Verify-then-Explain.

## (A) The change

Same family (`phi`), same prompt (`b4_vte/verifier` 1.0.0), same verdict rule,
same place in the pipeline. Only the model changes:

| | value |
|---|---|
| base model | `microsoft/phi-4` (14B, MIT licence) |
| build | Ollama library `phi4:14b-q4_K_M` (Q4_K_M, 9.05 GB) |
| weights blob | sha256 `fd7b6731…df20` |
| chat template blob | sha256 `32695b89…7c06a` |
| params blob | sha256 `45a1c652…ac80` (Phi-4's turn stop tokens only) |

The score step now runs its three models one at a time (verify all drafts,
then extract, then judge), so the larger verifier never shares the GPUs.

## (B) One more attempt, decided by a fixed rule

Before any Tier-A run is scored, Phi-4 verifies the **same 40 smoke drafts**
(38 distinct: two smoke instances produced identical prompts). The drafts
cannot be regenerated, since taxonomy 3.0.0 changes the detector, so
`tools/recheck_verifier.py` sends the verifier prompts stored in the smoke run's
ledger, unchanged, to the pinned Phi-4. For every draft it rejects, the author checks each stated reason against the
evidence list and the draft. A reason is *false* when:

- it calls a feature absent that is in the evidence;
- it gives the draft a direction the draft does not state; or
- it calls a magnitude invented where the draft states no number or strength
  for that feature.

A rejection is *wrong* when none of its reasons survives this check.

- If **more than half** of Phi-4's rejections are wrong, the verifier is
  declared unusable: H3 becomes exploratory, reported with the rule checker,
  and **no third model is tried**.
- Otherwise Phi-4 is the verifier for every Tier-A run.

The record (verdicts, reasons, the author's marks and the count) is committed
before the first Tier-A score session. The Phi-4-mini smoke run stays in the
record as the reason for this amendment; it is not citable.

## (C) What does not change

Everything else in amendment 0008: H3 in EXP-A-001, the void threshold sweep,
no-verdict replies read as unsupported, and the required reporting.
