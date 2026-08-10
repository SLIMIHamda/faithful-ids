# Annotation probe — 17 items

Extracted from `EXP-G-001_audit_v2` by `tools/build_annotation_probe.py`: the
items **Hamda** actually judged (17 items, 104 candidate
judgments). Not a gate run — EXP-G-001 needs 300 items and this is
17. What it *can* settle, cheaply, is whether an LLM annotator agrees
with a human well enough to be worth using at all, which is the decision that
comes before anyone commits to 300.

## Files

| file | what it is |
|---|---|
| `probe_matched.md` | same candidates + same 4 labels as the human saw — the head-to-head |
| `probe_freerecall.md` | the gate's real elicitation, no candidates — the harder test |
| `human_Hamda.json` | the human pass, verbatim |
| `probe_items.json` | the 17 items with their candidate lists |

## Running an LLM annotator

One **fresh conversation per model per prompt** — no shared context, no mention
of this project. Paste the whole file. Save the fenced JSONL to
`responses/<model>__matched.jsonl` or `responses/<model>__freerecall.jsonl`.

Run the same prompt on two different models to get a second and third opinion.

## Comparing

    python tools/compare_annotations.py --probe experiments/gates/EXP-G-001_audit_v2/probe_17

Reports pairwise agreement and Cohen's kappa, Krippendorff alpha, the specific
cells where annotators disagree, and each annotator scored against the extractor.

## Reading the result

`probe_matched.md` and `probe_freerecall.md` measure different things on purpose.
A model that agrees with the human on **matched** but collapses on
**freerecall** was working the list, not the text — and free recall is what the
gate actually asks for.

A caution already on the record: an LLM second annotator was tried on the v1
audit batch and **excluded** — Krippendorff alpha 0.02 against the human pass,
74% spurious `absent` on features that were verbatim in the text. That is the
outcome this probe exists to detect before it costs 300 items of anyone's time.
