# Amendment 0006 — the extractor prompt adopts the gold protocol's own rules

- **Date:** 2026-10-03
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file — made **before**
  any of the 300 items is extracted with the new prompt
- **Deciders:** project author (ruling), on a 12-item smoke test of amendment
  0005's runtime
- **Related:** [`0004-directional-evidence-rule.md`](0004-directional-evidence-rule.md)
  (the evidence rule and its section (E) on tuning),
  [`0005-extractor-weights-qat-gguf.md`](0005-extractor-weights-qat-gguf.md)
  (the runtime), [`../../extraction/eval_extractor.yaml`](../../extraction/eval_extractor.yaml)
  (now extractor 2.3.0, prompt 1.1.0),
  `experiments/gates/EXP-G-001_audit_v2/llm_annotation/chunk_01.md` (the gold
  protocol, as given to both annotators)

## Why

The 12-item smoke test of amendment 0005 (Kaggle, commit `4625daa`) showed that
the runtime works: the model ran fully on GPU and all 12 replies parsed. It also
showed the extractor prompt (`eval_extractor` 1.0.0) does not ask the question
the gold answers. On those 12 items the LLM path scored F1 0.82 where the rule
engine scored 1.00. Every error traces to one of three differences between the
prompt and the gold protocol:

| | prompt 1.0.0 (2026-07-05) | gold protocol (amendment 0004) |
|---|---|---|
| direction | relative to "the attack likelihood" | relative to "the score for the class it argues for" |
| no direction stated | not expressible: `+` or `-` only | `unclear` |
| names outside the vocabulary | "use the surface string verbatim" | vocabulary names only |

The prompt was written for the binary attack-vs-benign detector and predates
both the K-way detector and amendment 0004. So the model, following its prompt
correctly, flips the sign of every claim in a BENIGN text ("increases the BENIGN
score" → `-`). It invents a direction where the gold says `unclear`, and it
emits phrases like "traffic volume" as features. These are specification
mismatches, readable by putting the two documents side by side. They are not
weaknesses of the model.

## (A) The change

- **Prompt 1.1.0** (`prompts/extraction/eval_extractor/v1.1.0.md`) takes its
  direction rule, the `unclear` option, the "describing a value is not a
  direction" rule and the vocabulary rule from the gold protocol, nearly word
  for word. It keeps 1.0.0's output format (`feature`, `direction`, `rank`,
  `magnitude`) and its "parser, not a judge" framing. 1.0.0 stays in the
  registry, frozen.
- **Reply parsing** (extractor 2.3.0): `unclear` becomes a claim with no
  direction, stamped `default`, exactly as the rule engine records its own
  no-evidence claims. A feature name is mapped to the vocabulary the way the
  rule engine matches names (exact, then normalised or alias). Anything else
  is dropped.
- The rule engine, the weights, the runtime, the gold, the scorer's rule and the
  threshold (F1 ≥ 0.95) are unchanged.

## (B) Exposure to the evaluation data, and what binds it

The mismatch was seen on 12 of the 300 audit items: the first 12, `aud2-000` to
`aud2-011`. That is tuning informed by evaluation data, which 0004(E) asks to
disclose and bind:

- the new prompt text is **taken from the gold protocol**, not written to fix
  the 12 cases; nothing in it names a feature, generator or item from the smoke;
- **one revision, then score.** No further prompt change is made against the
  score. Any later change is a new logged attempt;
- **the verdict is on all 300 items**, as registered. Beside it the gate tool
  reports the same score **without the first 12 items**
  (`score_audit_gate.py --exclude-first 12`, written to
  `gate_result_excl_first12.json`). That is a sensitivity check, never the
  verdict. If the two land on opposite sides of 0.95, that is reported, not
  explained away;
- before the full run, the same 12 items are extracted once more with the new
  prompt. This confirms only that the replies parse and use the new options. It
  is not used to adjust anything.

## (C) Required reporting

Amendment 0005(C) applies unchanged, now naming instrument version 2.3.0 and
prompt 1.1.0. Add the 288-item sensitivity score and this amendment's exposure
statement wherever the gate result is reported.

## (D) Attempt log

Attempt 5 is the first full extraction of the 300 items with 2.3.0. The 12-item
smoke tests (2.2.0 with prompt 1.0.0; 2.3.0 with prompt 1.1.0) are not attempts.
Neither scores the gate.
