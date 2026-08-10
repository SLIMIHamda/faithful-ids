"""The annotation prompts, in ONE place.

`build_audit_batch.py` (the 300-item gate chunks) and `build_annotation_probe.py`
(the subset probe) previously carried their own copies of the free-recall
instructions. They said the same thing in different words, which is silently
corrosive: the probe measured Krippendorff alpha 0.850 between two LLM
annotators on the probe's wording, and that number only transfers to the gate run
if the gate asks for the task in exactly the same words. An agreement statistic
is a property of an instrument, and the wording IS the instrument.

So both builders import from here. Changing a prompt invalidates the agreement
measured under the previous one — say so in the changelog when you do.
"""

from __future__ import annotations

#: Free recall: no candidate list, name every feature the text claims. This is
#: the gate's elicitation — a candidate list would hand a model most of the
#: answer. Validated on the 17-item probe (alpha 0.850, GPT and grok).
FREE_RECALL = """# {title}

You are annotating explanation texts about network-traffic classification. Read
each text and report **what the text itself claims**. No other context is needed
and none is relevant.

## Task

For each item, list **every feature the text makes a directional claim about**,
and the direction the text asserts:

- `"+"` — the text says the feature raises / pushes up the score for the class it argues for
- `"-"` — the text says it lowers / pushes down that score
- `"unclear"` — the text names the feature but commits to no direction

Set `"hedged": true` when a direction is softened ("may slightly reduce").

## Rules

1. Report **only what the prose says**, not whether it is correct about the traffic.
2. Use the **canonical feature name** from the vocabulary below, even when the
   text paraphrases it ("maximum forward packet length" -> `Fwd Packet Length Max`).
3. A feature the text does not mention is simply left out. Do not emit `absent` rows.
4. If a text mentions no feature at all, emit `"claims": []`.
5. Output one JSON object per line (JSONL), one line per item, in the order
   given, inside a single fenced code block. No commentary.

## Output format

```jsonl
{{"item_id": "aud2-000", "claims": [{{"feature": "Flow Duration", "dir": "+", "hedged": false}}]}}
```

## Feature vocabulary (use these exact names)

{vocab}

---

## Items

"""

#: Matched: the same candidate list and the same four labels a human sees in
#: annotator.html, so every judgment lines up with a human judgment. Higher
#: agreement (alpha 0.894 on the probe) but it shows the model which features
#: the extractor claimed, so it is a COMPARISON instrument, not gate gold.
MATCHED = """# {title}

You are annotating explanation texts about network-traffic classification. Read
each text and report **what the text itself claims**. No other context is needed
and none is relevant.

## Task

Each item gives a text and a list of features. For **every feature in the list**,
say what the text claims about that feature's effect on the score for the class
the text is arguing for:

- `"+"` — the text says this feature raises / pushes up that score
- `"-"` — the text says it lowers / pushes down that score
- `"unclear"` — the text names the feature but commits to no direction
- `"absent"` — the text does not discuss this feature at all

Some listed features are **not** in the text. `absent` is the correct answer for
those and is expected to occur.

Also set `"hedged": true` when the text gives a direction but softens it
("may slightly reduce", "possibly raises").

## Rules

1. Report **only what the prose says**. Do not judge whether the text is correct
   about the traffic — that is a different question and is not being asked.
2. A text may paraphrase a feature ("maximum forward packet length" for
   `Fwd Packet Length Max`). A paraphrase still counts as discussing it.
3. Answer for **every** listed feature of every item. Do not add features.
4. Output one JSON object per line (JSONL), one line per item, in the order
   given, inside a single fenced code block. No commentary before or after.

## Output format

```jsonl
{{"item_id": "aud2-000", "claims": [{{"feature": "Flow Duration", "dir": "+", "hedged": false}}]}}
```

---

## Items

"""
