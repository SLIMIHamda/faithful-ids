#!/usr/bin/env python3
"""Extract the items one annotator actually judged, as prompts for other annotators.

A full 300-item pass is expensive. This takes whatever subset somebody really
annotated and builds the materials to have other annotators — human or LLM —
judge **exactly those items**, so the passes are comparable one judgment at a
time rather than only in aggregate.

Two prompts are emitted, because they answer different questions:

``probe_matched.md``
    The same candidate list the first annotator saw, and the same four labels
    (``+`` / ``-`` / ``unclear`` / ``absent``). Every judgment lines up with a
    judgment the first annotator made, so agreement is computable per cell. This
    is the head-to-head comparison.

``probe_freerecall.md``
    The gate's real elicitation: no candidates, name every feature the text
    claims. Harder, and the only one that measures whether an annotator can do
    the task without being handed most of the answer. An LLM that does well
    matched and badly here was reading the list, not the text.

Neither prompt contains the extractor's output — same blinding as the batch.

Run::

    python tools/build_annotation_probe.py --annotations <export.json> \\
        --batch experiments/gates/EXP-G-001_audit_v2 --out <dir>
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

LABELS = "`+` (raises / pushes up), `-` (lowers / pushes down), `unclear` (named but no direction), `absent` (not discussed in the text)"


def load_batch(batch_dir: Path) -> dict[str, dict]:
    return {
        it["item_id"]: it
        for line in (batch_dir / "audit_batch.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
        for it in [json.loads(line)]
    }


def judged_items(annotations: dict) -> list[str]:
    seen: list[str] = []
    for row in annotations["annotations"]:
        if "feature" in row and row["item_id"] not in seen:
            seen.append(row["item_id"])
    return seen


MATCHED = """# Annotation task — {n} explanation texts

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

FREE = """# Annotation task — {n} explanation texts

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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--annotations", type=Path, required=True)
    p.add_argument("--batch", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)

    ann = json.loads(args.annotations.read_text(encoding="utf-8"))
    batch = load_batch(args.batch)
    vocab = sorted(json.loads((args.batch / "feature_vocabulary.json").read_text(encoding="utf-8")))
    ids = judged_items(ann)
    missing = [i for i in ids if i not in batch]
    if missing:
        raise SystemExit(f"annotation references items not in the batch: {missing}")

    out = args.out
    (out / "responses").mkdir(parents=True, exist_ok=True)

    n_cells = 0
    matched = [MATCHED.format(n=len(ids))]
    free = [FREE.format(n=len(ids), vocab="\n".join(f"- `{v}`" for v in vocab))]
    for iid in ids:
        it = batch[iid]
        cands = it["candidates"]
        n_cells += len(cands)
        matched.append(f"### {iid}\n\n```\n{it['explanation_text']}\n```\n\nFeatures to judge:\n"
                       + "\n".join(f"- `{c}`" for c in cands) + "\n")
        free.append(f"### {iid}\n\n```\n{it['explanation_text']}\n```\n")

    tail_m = (f"---\n\nNow output exactly {len(ids)} JSONL lines, one per item from "
              f"`{ids[0]}` to `{ids[-1]}`, each answering for every listed feature of that "
              f"item ({n_cells} judgments in total), in one fenced block.")
    tail_f = (f"---\n\nNow output exactly {len(ids)} JSONL lines, one per item from "
              f"`{ids[0]}` to `{ids[-1]}`, in one fenced block.")
    (out / "probe_matched.md").write_text("\n".join(matched) + "\n" + tail_m, encoding="utf-8")
    (out / "probe_freerecall.md").write_text("\n".join(free) + "\n" + tail_f, encoding="utf-8")

    human = out / f"human_{ann['annotator']}.json"
    shutil.copyfile(args.annotations, human)
    subset = {iid: batch[iid] for iid in ids}
    (out / "probe_items.json").write_text(
        json.dumps(subset, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    (out / "README.md").write_text(f"""# Annotation probe — {len(ids)} items

Extracted from `{args.batch.name}` by `tools/build_annotation_probe.py`: the
items **{ann['annotator']}** actually judged ({len(ids)} items, {n_cells} candidate
judgments). Not a gate run — EXP-G-001 needs 300 items and this is
{len(ids)}. What it *can* settle, cheaply, is whether an LLM annotator agrees
with a human well enough to be worth using at all, which is the decision that
comes before anyone commits to 300.

## Files

| file | what it is |
|---|---|
| `probe_matched.md` | same candidates + same 4 labels as the human saw — the head-to-head |
| `probe_freerecall.md` | the gate's real elicitation, no candidates — the harder test |
| `human_{ann['annotator']}.json` | the human pass, verbatim |
| `probe_items.json` | the {len(ids)} items with their candidate lists |

## Running an LLM annotator

One **fresh conversation per model per prompt** — no shared context, no mention
of this project. Paste the whole file. Save the fenced JSONL to
`responses/<model>__matched.jsonl` or `responses/<model>__freerecall.jsonl`.

Run the same prompt on two different models to get a second and third opinion.

## Comparing

    python tools/compare_annotations.py --probe {out.as_posix()}

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
""", encoding="utf-8")

    print(f"probe: {len(ids)} items, {n_cells} candidate judgments -> {out}/")
    print(f"  probe_matched.md      head-to-head with {ann['annotator']}")
    print("  probe_freerecall.md   the gate's real task")
    print(f"  human_{ann['annotator']}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
