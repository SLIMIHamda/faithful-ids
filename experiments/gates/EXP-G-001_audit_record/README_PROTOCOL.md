# Extractor audit batch v1 — blind protocol

**Goal.** Disambiguate the b4 3B→8B DSA regression (63/150 instances worse, p=1.2e-16) between three
hypotheses, and double as the interim extractor prose-coverage audit (step 5).

- **Branch 1 (verifier gap):** the explanation text asserts genuinely wrong signs; the sign-blind
  rule-verifier passes them.
- **Branch 2 (extractor gap):** the text asserts *correct* signs but the 1.1.0 extractor mis-parses
  the larger model's richer prose.
- **Branch 3 (generation gap, pre-verifier):** b4's *internal* claims already carry wrong signs
  before the verifier sees them (constraint-adherence-vs-fluency failure).

## Annotator task (blind — do NOT open `audit_key_DO_NOT_SHOW_ANNOTATOR.json`)
`audit_batch.jsonl` = 150 shuffled items. Group and generator are hidden. For each claim, do **one**
judgment: read `explanation_text` and set `text_asserts_direction` to what **the text itself claims**
for that feature — `"+"` (pushes toward attack / raises risk), `"-"` (toward benign / lowers risk),
`"unclear"`, or `"absent"` (text doesn't actually mention it). Ignore `shap_sign` and
`extracted_direction` while judging — report only what the prose says.

## Derived after annotation (not by the annotator)
- `extractor_correct = (extracted_direction == text_asserts_direction)` → extractor fidelity to prose.
- `text_correct = (text_asserts_direction == shap_sign)` where `shap_sign` is present (top-5 only).

## Reading the result
- **Degraded extractor-error rate ≫ control** → **Branch 2** (extractor gap). Free fix; no tokens.
- **Extractor-error equal, but `text_correct` lower on degraded** → **Branch 1 or 3** (genuine).
  Splitting them needs b4's internal verifier inputs, which are **NOT in these artifacts** (metadata
  is empty; no `verifier_outputs/`). That requires adding verifier-trace logging to b4 + regeneration
  (costs tokens) — do it only if this branch is reached.

Look specifically for **paraphrase-driven sign softening** in the degraded (larger-model) transcripts:
hedged/implicit direction around a correct claim is the fingerprint of the fluency-vs-constraint
mechanism (points to Branch 3, fix is constraint-side generation, not just verifier-side).

`shap_sign` covers only the b0 top-5 (full attribution not exported); `text_correct` is derivable on
those. `extractor_correct` is derivable for **all** claims — and it alone separates Branch 2 from {1,3}.
