# Amendment 0004 — a directional claim requires explicit textual evidence

- **Date:** 2026-08-10
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made **before**
  the re-elicitation it requires, and before any gold is scored under the rule
- **Deciders:** project author (ruling), on evidence from the 300-item
  double-LLM annotation of `EXP-G-001_audit_v2` (commit `e9f3b71`)
- **Related:** [`../decision_thresholds.yaml`](../decision_thresholds.yaml)
  (frozen `extractor_f1` = 0.95),
  [`../../extraction/eval_extractor.yaml`](../../extraction/eval_extractor.yaml)
  (the instrument under audit),
  [`0003-estimand-and-removal-operator.md`](0003-estimand-and-removal-operator.md),
  `experiments/gates/EXP-G-001_extractor_audit.yaml`

## Why

Two LLM annotators independently annotated all 300 items of the EXP-G-001 audit
batch. They agreed on **1836 of 1842 cells (99.7%)** about *which* features are
claimed and in *which* direction. Krippendorff alpha over the raw labels was only
**0.707**, and **98% of the entire disagreement was one distinction**: 292 cells
where one annotator wrote `unclear` and the other wrote `+`.

The disagreement is not noise and it is not spread out. It sits in one generator
— `b2_zeroshot`, 258 of 349 cells (74%), against 0% for `b0`/`b1`/`b1l` — because
b2 writes **value descriptions rather than score effects**:

> "A high **PSH Flag Count** (1.0) suggests potential payload manipulation
> typical of botnet activity."

Does that text *assert* that the feature raises the Bot score, or does it name
the feature without committing? The frozen protocol did not say, and the answer
decides the gate:

| gold reading | extractor precision | recall | F1 |
|---|---|---|---|
| lenient (value description asserts a direction) | 0.970 | 0.980 | **0.975** |
| strict (explicit evidence required) | 0.741 | 0.990 | **0.848** |

A threshold that a single unwritten instruction moves by 13 F1 points is not
pre-registered. This amendment writes the instruction.

## (A) The rule

> **A claim is directional only when the text provides explicit directional
> evidence for it.** Where the text names a feature without committing to a
> direction — including describing its *value* ("is high", "is unusually large")
> without stating an effect on the score — the direction is **`unclear`**, and
> the claim does not enter the directional set.
>
> **Inference by default is never directional evidence.** A direction the
> extractor supplies because it found no cue (`direction_evidence: "default"`)
> is not a parsed claim, and gold never counts it as one.

Explicit evidence is judged by the annotator reading the prose, **not** by
whether the extractor's lexicon happens to contain the cue. A text that says a
feature "added to the score" carries explicit evidence even though the 1.4.0
lexicon misses that verb — that gap is an instrument defect the gate exists to
find, not a property of the gold.

**The strict reading is chosen deliberately, knowing it fails the gate.** Under
the lenient reading EXP-G-001 passes at F1 0.975 — while **403 of the
extractor's 1183 directional claims (34%) are defaults**, guesses that score as
correct because `+` is the base rate. A gate that certifies an instrument
guessing a third of its answers is measuring nothing. The rule is set so the
gate is capable of failing; that is the only property that makes passing it
informative.

## (B) Gold must be re-elicited; nothing already collected is gold

Both existing 300-item LLM passes, and the 17-item human pass, were elicited
under the **previous** wording ("the text names the feature but commits to no
direction"). They split on interpreting it. One of them happens to behave like
the rule above.

**Adopting that pass as gold because it matches the rule just written would
reintroduce the researcher degree of freedom this amendment exists to close**,
one level up. So:

- The gold for EXP-G-001 is **re-elicited** with the rule stated verbatim in the
  annotation prompt. Passes collected before this amendment are **calibration
  evidence**, not gold, and are retained under `llm_annotation/responses/` with
  the protocol version they were collected under.
- The 17-item human pass is **previous-protocol data**. It may inform
  calibration and must not silently become gold. Human gold under this rule
  requires re-annotation under the revised instructions.

## (C) Required reporting

Every EXP-G-001 verdict reports, together and never separately:

1. overall precision, recall and F1 against adjudicated gold;
2. the same three **split by `direction_evidence`** — `word` / `number` /
   `default` — so a headline number cannot hide its composition;
3. the **count and proportion of extractor claims resting on `default`**.

(3) is the statistic that made the lenient reading untenable and it is now a
standing part of the verdict, not a diagnostic someone has to think to compute.

## (D) Attempt log

Amendment 0001's gate-failure clause governs: **the instrument iterates, the
annotation is fixed, and every attempt is logged.** Attempts so far:

| # | date | extractor | gold | F1 | verdict |
|---|---|---|---|---|---|
| 1 | 2026-08-10 | 1.4.0 | pre-amendment LLM pass, strict reading | 0.848 | **FAILED** (below 0.95) |

Attempt 1 is recorded as a failure even though its gold does not meet (B),
because a result that looked like a pass under the lenient reading must not
vanish from the record now that the strict reading is registered.

## (E) Instrument iteration: what was tried, and what it was worth

The first hypothesis was lexicon coverage. `_POS_WORDS` held five stems
(`increas`, `rais`, `higher`, `elevat`, `push`) and `_NEG_WORDS` three, so
directional verbs like "added to" and "drove" fell through to the default.
Extractor **1.5.0** widens both lists.

**Measured, it is worth almost nothing: defaults fall 403 → 393 of 1183 claims,
a share of 34.1% → 33.2%.** The lexicon was not the problem. Recording the
negative result because it changes the diagnosis: the extractor defaults on that
prose because **the prose genuinely carries no directional cue**, which is
exactly the case rule (A) says is `unclear`. There is no wording to catch.

Two things follow, and they are the substance of this amendment:

1. **The rule applies symmetrically, to prediction as well as gold.** A claim
   whose direction the extractor supplied by default is not a directional claim
   *on either side of the comparison*. The instrument already records this —
   `direction_evidence` exists (extractor 1.3.0) precisely so a defaulted sign is
   identifiable — so the scorer excludes `default`-derived claims from the
   prediction set. No change to the extractor's output contract is needed, and
   none is made: `ClaimTuple.direction` stays mandatory.
2. **The gate may still fail, and that is not a reason to loosen the rule.**
   Against pre-amendment gold, excluding defaults gives precision 0.932, recall
   0.821, F1 0.873. Whether correctly re-elicited gold clears 0.95 is unknown and
   is not to be predicted here.

**Disclosed risk on the lexicon change:** the candidate terms were suggested by
reading prose in the audit set that also scores the repaired instrument — tuning
informed by evaluation data. Binding mitigations:

- additions are **generic directional verbs of English** chosen as a class, not
  harvested from the cells that failed;
- **direction-transparent connectives are excluded on principle** — "contributed
  to", "added to", "drove", "supports" take their polarity from the object that
  follows, so as bare cues they mis-sign "contributing to a *reduced* risk"
  (a first draft included them and a regression test caught it). The consequence
  is accepted: "added to the attack score" still defaults, which under rule (A)
  is a **miss**, not a wrong sign;
- the lexicon is **not iterated against the score** — one revision, then
  re-score; any further revision is a new logged attempt;
- the exposure is stated wherever the gate result is reported.

A clean-room alternative — deriving the lexicon from a held-out corpus — is the
stronger design and is **not** what was done. That is a limitation of this gate,
stated rather than hidden. Given (E)'s measured result, it is also close to
moot: the lexicon is not where this gate is decided.
