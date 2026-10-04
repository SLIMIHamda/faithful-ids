# Verifier re-check record (amendment 0010(B))

The one further attempt amendment 0010 allows: does the pinned Phi-4 (14B) judge
the same smoke drafts that Phi-4-mini rejected wholesale, without false
rejections?

## Inputs

- `phi4_mini_smoke2/ledger.jsonl` — the 38 distinct verifier calls of the
  2026-10-03 score smoke run (Kaggle kernel `faithfulids-tier-a` v4, commit
  `d02c8ab`, Qwen3-8B drafts, N=20, B4 + B5 = 40 drafts, two pairs identical).
  Phi-4-mini, `phi4-mini:3.8b-q4_K_M`. Every reply's verdict line is
  `UNSUPPORTED`, with reasons false on their face (amendment 0010, "Why").

## The run

- Kaggle kernel `faithfulids-verifier-recheck` v1, commit `1394569`, one T4,
  Ollama 0.35.1, 2026-10-04. `tools/recheck_verifier.py` sent each stored prompt,
  with its stored params, to `phi4:14b-q4_K_M` (blobs checked against the pins).
- `phi4_14b/ledger/ledger.jsonl` — the 38 Phi-4 replies (mean 317 tokens,
  28 s per call on a T4).

## Result

| reader | Phi-4-mini | Phi-4 (14B) |
|---|---|---|
| first reader (whole-reply word search) | 38 UNSUPPORTED | 38 UNSUPPORTED |
| verdict line, as the prompt asks (amendment 0011) | 38 UNSUPPORTED | **38 SUPPORTED** |

Every Phi-4 reply works through the prompt's three checks (features present,
directions match, no invented magnitudes) and ends with the line `SUPPORTED`.
The first reader called all 38 unsupported because each reply repeats check 3,
"Are there unsupported or invented magnitude claims?", before answering it.
Amendment 0011 fixes the reader. `phi4_14b/summary.json` and
`phi4_14b/review.csv` are the re-read of the same recorded replies with the
fixed reader (`--mode replay`, no model call).

## Decision under amendment 0010(B)

Phi-4 rejects **0** of the 38 drafts, so there is no rejection to mark and none
is wrong. **Phi-4 is the verifier for every Tier-A run.** These drafts are ones
the extractor scores as faithful (Layer-1 mention F1 1.0), so approving all of
them is the expected behaviour. How often the verifier rejects unfaithful
drafts is a Tier-A result, not a smoke one.
