# EXP-G-001 — extractor audit record (interim, batch v1)

*Committed 2026-07-14. Instrument at time of writing: extractor **1.4.0**.*

## What this is — and what it is NOT

This folder is the **provenance record of the blind human audit** that motivated and
validated the extractor repairs `1.1.0 → 1.4.0`. It is committed so the instrument's
validity trail is public and re-runnable.

> **STATUS: this is diagnostic + interim-validity evidence, NOT a formal EXP-G-001
> gate pass.** The registered gate ([`../EXP-G-001_extractor_audit.yaml`](../EXP-G-001_extractor_audit.yaml))
> requires **300 items, 2 annotators, an adjudicated gold standard, F1 ≥ 0.95, and a
> Krippendorff-α inter-annotator report**. This audit was **150 items, one human
> annotator**, scoring **directional agreement** (extractor-vs-prose and prose-vs-SHAP),
> not F1 against adjudicated gold. It therefore does **not** discharge the gate:
> **EXP-G-001 remains `registered`, not `passed`**, and the formal dual-annotated run
> against extractor 1.4.0 is still owed before any Tier-A citability.

## Why it was run

Two goals ([`README_PROTOCOL.md`](README_PROTOCOL.md)):

1. **Disambiguate the B4 3B→8B "DSA regression"** (63/150 instances worse, paired sign
   test p = 1.2e-16) between three branches — (1) verifier gap, (2) extractor gap,
   (3) generation gap (pre-verifier sign errors).
2. Double as an **interim extractor prose-coverage audit** for the pilot.

150 blind-shuffled items: **63 degraded** (B4@8B, the regression set) + **63 control** +
**24 B3 distractor**. Group and generator hidden behind
[`audit_key_DO_NOT_SHOW_ANNOTATOR.json`](audit_key_DO_NOT_SHOW_ANNOTATOR.json) (now
revealed — the audit is complete). The annotator reported only what each explanation's
prose asserts for each feature, blind to the extractor output and the SHAP sign.

## Result — Branch 2 (instrument artifact)

Reproduce: `python score_audit.py scored_human.jsonl` (reads `audit_batch.jsonl` + the key).

| group | n | extractor_correct | text_correct (top-5, dir.) | hedged |
|---|---|---|---|---|
| control | 221 | 0.950 (210/221) | 0.995 (216/217) | 0 |
| degraded | 238 | **0.567 (135/238)** | **1.000 (230/230)** | 0 |
| distractor | 117 | 0.974 (114/117) | 0.991 (114/115) | 0 |

- **Extractor-error rate 43.3% on degraded vs 5.0% on control** (Fisher p = 1.9e-23),
  while the **text's directional claims are ~100% correct everywhere** → the fault is the
  **extractor parsing prose**, not the model writing wrong signs, and not the verifier.
- **All 117 extractor disagreements are `extracted = "+"`** — the default-POSITIVE branch.
- **Zero hedged claims** (0/576): there is no paraphrase-driven "sign-softening" mechanism.
- **Root cause:** the direction lexicon held only inflected forms, so Qwen3-8B-B4's dominant
  phrasing "has a **decreasing** effect on the attack score" matched no cue and fell to
  default-POSITIVE ("increasing" fell through identically but was accidentally correct).
  63/63 degraded items contain "decreasing" vs 6/63 control — the selection loop that
  *created* the "degraded" label.

## Consequences (already landed)

- **Retired claims:** "B4's directional faithfulness degrades with capability" and
  "Layer-1 DSA caught the sign-blind verifier" — both were measuring the extractor.
  Branches 1 and 3 are falsified: no verifier-trace logging or B4 regeneration was needed
  to resolve the regression (that logging was later added for the *abstention* story, not
  this one).
- **Extractor fixes** validated against this same human reading: `1.2.0` (stem-matched
  direction cues) → 99.5% agreement (560/563 over the cached corpora); `1.3.0`
  (sentence-bounded window) and `1.4.0` (paraphrase aliases) held ≥ 99.5%. See
  [`../../../CHANGELOG.md`](../../../CHANGELOG.md).

## Second annotator excluded (provenance)

A second, **LLM** annotator (Meta MUSE) was run ([`llm_annotation/`](llm_annotation/),
scored to [`scored_muse.jsonl`](scored_muse.jsonl)) and **excluded**: κ = 0.02 vs the human,
with 74% spurious "absent" on verbatim-present features. The exclusion — and the machinery
that caught it — is itself audit provenance; it does **not** count toward the gate's
2-annotator requirement (MUSE is not a qualified human annotator).

## File manifest

| file | role |
|---|---|
| `README_PROTOCOL.md` | the blind annotation protocol given to the annotator |
| `audit_batch.jsonl` | 150 shuffled items (group/generator hidden) |
| `audit_key_DO_NOT_SHOW_ANNOTATOR.json` | group + generator key (revealed post-audit) |
| `annotator.html` | the offline annotation UI used to collect judgments |
| `scored_human.jsonl` | merged per-claim result (576 claims) — the audit's primary output |
| `scored_muse.jsonl` | merged MUSE result (excluded, κ=0.02) |
| `score_audit.py` | scorer: merges annotations + batch + key → `scored_<annotator>.jsonl` |
| `llm_annotation/` | MUSE prompt chunks, responses, and the validator (exclusion provenance) |

## Still owed for Tier-A

The **formal EXP-G-001**: 300 items, 2 human annotators, adjudicated gold, F1 ≥ 0.95 +
Krippendorff α, scored against **extractor 1.4.0**. Until then the gate is `registered`
and no Tier-A run may cite a passed EXP-G-001.
