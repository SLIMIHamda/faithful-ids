# Reproducing this artifact

Four reproduction tiers, from "trust nothing, rebuild from raw" (L4) to
"regenerate the figures in half an hour" (L1). CI continuously exercises **L1**
and an **L3 smoke slice**; the artifact-evaluation submission targets **L1–L3**.

Everything runs inside the pinned container (`environment/Dockerfile`, referenced
by digest in every run manifest). Run all commands through the `Makefile`.

| Tier | What is reproduced | From | Needs | Time |
|---|---|---|---|---|
| **L1** | Every figure & table in the paper | released `analysis/outputs/` | container, CPU | < 30 min |
| **L2** | Every statistic | released `runs/` artifacts | container, CPU | hours |
| **L3** | Every metric incl. Layer-1/2, from explanations | released caches + LLM ledger (replay mode) | container, CPU | hours |
| **L4** | Everything from raw data | public datasets + open weights + API access | GPU, API keys | days |

## Tolerance policy (what must be byte-identical vs. bounded)

Reproducibility is **not** a promise of universal bit-stability — it is a
disclosed, tested boundary (hostile-audit A2).

- **Byte-identical (CI-enforced):** frozen splits, TreeSHAP attributions from
  frozen tree models on CPU, all statistics, all figures/tables, the toy
  pipeline's metrics (determinism-smoke gate).
- **Tolerance-bounded (documented per artifact):** GPU DeepSHAP attributions,
  open-weights LLM generations (stochasticity protocol k=3), frontier-API
  outputs (replay-verifiable via the ledger, not re-executable).

Per-artifact tolerances live in `docs/reproducibility-guide.md`.

## L1 — figures & tables from analysis outputs (< 30 min, CPU)

```bash
make reproduce-l1
```

Regenerates every asset under `paper/**/generated/` from the released
`analysis/outputs/`; CI (`figure-regen.yml`) diffs the regenerated hashes
against the committed ones. This is the `artifact/reviewer_kit/` path.

## L2 — statistics from run artifacts (hours, CPU)

```bash
make analyse H=h1_gap        # recompute one hypothesis' statistics
make analyse-all             # recompute every analysis config
```

Each analysis config enumerates the **exact** run IDs it consumes (no globs) and
references pre-registered tests/thresholds by config path. Outputs are
manifested and hash-verified (`stats-regen.yml`).

## L3 — metrics from explanations via the LLM ledger (hours, CPU)

```bash
make reproduce-l3            # cache-only replay: no network, no GPU, no API
```

The append-only LLM call ledger (`data/cache/llm_calls/`) stores every
request/response with its pinned model-snapshot ID. Replay mode recomputes every
Layer-1/Layer-2 metric from stored explanations. API-model numbers are labelled
*replay-verifiable*; open-weights numbers are *re-executable*.

## L4 — everything from raw data (days, GPU + API keys)

Datasets are **not** redistributed. Acquire them from the public sources, then
let the deterministic, checksummed pipeline reconstruct the corrected corpus.

### Dataset acquisition

| Dataset | Source | Role |
|---|---|---|
| CICIDS2017 | Canadian Institute for Cybersecurity (UNB) | anchor (corrected) |
| UNSW-NB15 | UNSW Canberra | Tier A second dataset |
| CSE-CIC-IDS2018 | CIC / AWS Open Data | Tier B transfer only |

```bash
# 1. Place the downloaded originals under data/raw/<dataset>/ (read-only)
# 2. Register + verify checksums, then run the full chain:
make data DATASET=cicids2017_corrected     # raw -> corrected -> processed -> splits
make run EXP=EXP-G-001                      # extractor-audit gate (must PASS)
make run EXP=EXP-G-002                      # RQ0 calibration gate (must PASS)
make run EXP=EXP-A-001                      # Tier A core factorial (44 cells)
```

`data-integrity.yml` verifies the chain: download checksums → corrected
checksums → processed checksums. Any gate that fails aborts the downstream run —
orchestration refuses Layer-1 metric computation without a passing gate run ID.

## Where a reviewer should start

`artifact/reviewer_kit/` (L1 quickstart, < 30 min) and
`docs/reviewer-guide.md` ("verify Table 3 in 10 minutes" recipes).
