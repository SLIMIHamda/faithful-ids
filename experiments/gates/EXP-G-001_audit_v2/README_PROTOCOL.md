# EXP-G-001 extractor audit — blind protocol (extractor_audit_v2)

Built 2026-08-21 by `tools/build_audit_batch.py`
from run `EXP-PILOT-001__3309768__2026-07-25T1354Z`, extractor **1.4.0**, seed **3001**
(`seeds:gates:extractor_audit`). Regenerating with the same run and seed
reproduces this batch byte for byte.

## What this gate measures

`experiments/gates/EXP-G-001_extractor_audit.yaml` asks: does the evaluation
claim extractor reach **F1 >= 0.95 against adjudicated gold** on 300
dual-annotated items? F1 is over **(feature, direction) pairs**:

* **gold** — every directional claim two annotators agree the *text* makes,
  after adjudication of their disagreements;
* **prediction** — the claims the extractor produced for that same text.

This is a question about the **instrument**, not about the model. Whether the
text is *right* about the traffic is a different question and is not asked here.

## Why the candidate list is not the extractor's output

The v1 batch listed exactly the features the extractor had claimed and asked only
for their direction. That can measure a claim the extractor got wrong; it can
never measure one it **missed**, so recall — and therefore F1 — was not
computable. Each item here instead lists

* every vocabulary feature whose canonical name or a registered alias appears in
  the text under lenient matching (this over-generates deliberately),
* every feature the extractor claimed,
* plus 2 features the text does not mention,

shuffled. 1825 candidate judgments in total, 6.1 per item.
**The annotator can add any feature the text claims that is not listed** — that
addition is what makes recall measurable. The extractor's output appears nowhere
in `audit_batch.jsonl`, in `annotator.html`, or in the LLM chunks: it is only in
`audit_key_DO_NOT_SHOW_ANNOTATOR.json`. Blindness is structural, not requested.

## Sampling design (fixed before the items were seen)

| stratum | items |
|---|---|
| `b0_raw_shap` | 15 |
| `b1_template` | 15 |
| `b1l_llm_render` | 40 |
| `b2_zeroshot` | 50 |
| `b3_dte_style` | 60 |
| `b4_vte` | 60 |
| `b5_narrative_vte` | 60 |

`b4_vte` and `b5_narrative_vte` are censused: they carry the hardest prose and
the one open directional uncertainty. `b0_raw_shap` and `b1_template` are
deterministic templates and act as a **litmus stratum** — an annotator who
disagrees with the extractor *there* has misread the task rather than found a
defect. Check that stratum first before trusting the rest of a pass.

## The annotator's task

Open `annotator.html` in any browser. It needs no network and saves to that
browser as you go; **export when you finish**. For each listed feature, record
what the text claims: `+` raises, `-` lowers, `unclear` (named, no direction),
`absent` (not discussed). Tick *hedged* when a direction is softened. Add any
feature the text claims that is not on the list.

Two annotators work **independently** and must not compare notes before both
exports exist. Disagreements are adjudicated afterwards; the adjudicated set is
the gold. Krippendorff alpha is computed on the two independent passes, before
adjudication — adjudicating first would erase the disagreement the statistic
exists to report.

## The LLM annotator

`llm_annotation/` holds 12 self-contained prompts. One fresh conversation
per chunk, no shared context. Save each fenced JSONL reply to
`llm_annotation/responses/<model>/chunk_NN.jsonl`, then run
`python llm_annotation/validate_llm_annotations.py responses/<model>` to check
completeness and merge.

**The two annotators are elicited differently, and that is deliberate.** The
human UI presents a candidate list and asks for a judgment on each; the LLM is
asked for free recall against the vocabulary. A candidate list would hand a
language model most of the answer, and free recall would make a human's pass
slow and inconsistent. Both modes produce the same object — a set of
(feature, direction) claims about the text — so both score against gold the same
way. For agreement, the unit set is every (item, feature) pair either annotator
names, with "not claimed" as an explicit category; a feature one annotator lists
and the other omits is a disagreement, not a missing value. Report the
elicitation difference with the alpha: it is a plausible source of systematic
disagreement and a reader should not have to discover it from the code.

**A caution that is on the record.** A second LLM annotator was already tried on
the v1 batch and **excluded**: Krippendorff alpha 0.02 against the human pass,
with 74% spurious `absent` judgments on features that were verbatim in the text.
Check the litmus stratum before accepting any LLM pass as an annotator. An LLM
that disagrees with the deterministic `b0`/`b1` templates is not annotating.

## Gate-failure clause (prereg amendment 0001)

If the gate fails, the legal move is: **the instrument iterates, the annotation
is fixed, and every attempt is logged.** The extractor may be revised and
re-gated (semver bump, changelog, re-run). The gold set is never edited to meet
the threshold. Every attempt is recorded whether it passes or not.
