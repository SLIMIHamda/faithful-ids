# Kaggle pilot launcher

> **Tier-A (EXP-A-001):** `tier_a/` holds its own notebook and
> `kernel-metadata.json`. Tier-A runs in two steps because a generator and the
> certified extractor (Gemma via Ollama) do not fit one 2x T4 session:
> `PHASE='generate'` (one model per session, resumable, repeat until the log says
> `generation COMPLETE`), then `PHASE='score'` (EXP-G-001 token, EXP-G-002,
> replay + LLM extraction + metrics + run). Carry `tier_a/ledgers/` between
> sessions as a private dataset input. Budget: ~2,000 generation calls per model
> at N=400, i.e. one to several 12 h sessions per model on T4s.
>
> The score step serves three pinned models under Ollama, one at a time: the
> B4/B5 verifier (Phi-4, amendments 0008 + 0010), the extractor (Gemma, 0005) and
> the plausibility judge (Command R7B, 0009). Each keeps its own ledger under
> `tier_a/ledgers/{verifier,extraction,judge}/`.
>
> **Verifier re-check (amendment 0010):** `verifier_recheck/` sends the verifier
> prompts stored in the 2026-10-03 smoke run's ledger to the pinned Phi-4 and
> writes `review.csv` for the author to mark. One T4, no dataset but the ledger
> dataset, ~20-30 min.
>
> **Extractor re-gate (EXP-G-001):** `extractor_regate/` holds its own notebook
> and `kernel-metadata.json`. It needs no dataset: 2x T4, Internet on. Push it
> from a terminal with `kaggle kernels push -p kaggle/extractor_regate`. See
> amendment 0005 for why it serves the extractor through Ollama.

`kaggle_pilot_launcher.ipynb` is an **execution wrapper only** — it contains no
experimental logic. It clones this repository at a pinned tag, installs it,
points it at a CICIDS2017 dataset, and invokes the repository's own CLI. All
science (data cleaning, XGBoost training, TreeSHAP, B0–B4 generation, extraction,
verification, metrics, artifact writing) runs **inside the repository**
(`faithfulids.orchestration.execute.run_pilot`, launched by
`faithfulids.orchestration.cli run --experiment EXP-PILOT-001`).

## What it produces (real, at Kaggle scale)

CICIDS2017 → XGBoost → exact **TreeSHAP** → **B0–B4** explanations (B2/B3/B4 via
one 4-bit instruct LLM) → rule-assisted extraction → **Layer-1** (mention P/R/F1,
DSA, ARC, HFR) + **Layer-2** erasure (conditional-expectation imputation) + cost,
written to a hash-manifested run in `runs/EXP-PILOT-001/`. Then Friedman+Nemenyi
across B0–B4, a critical-difference diagram, a B4 coverage-risk curve, and a
per-generator faithfulness table.

## Usage

1. New Kaggle notebook → **Add Input** → search **CICIDS2017** (the raw CIC
   `MachineLearningCVE` CSVs or an upstream-corrected variant both work).
2. Enable **GPU** (T4 is enough for a 7B model in 4-bit).
3. No HF token needed for the default (ungated) Qwen model. Only add an
   `HF_TOKEN` Kaggle Secret if you switch to a gated model (e.g. Mistral/Llama).
4. Paste/upload this notebook and **Run All**. It auto-detects the CSV directory,
   runs the pilot, and displays the results inline; artifacts are zipped to
   `/kaggle/working/pilot_artifacts.zip`.

## Python version on Kaggle

Kaggle's image runs Python 3.13. `pyproject.toml` keeps `>=3.11,<3.13`, because
that range describes the exact pinned stack, and two of its pins (pyarrow 17.0.0,
shap 0.46.0) have no 3.13 builds. All three notebooks install the repo with
`--no-deps --ignore-requires-python`, so they run on Kaggle's own library
versions; the pilot launcher records what actually ran in `env-fingerprint.json`
and `environment.txt`. Their install cells use `set -o pipefail` and import
`faithfulids` right after the install, so a failed pip step stops the session
instead of scrolling past.

## Knobs (set in the notebook's first code cell)

| Env var | Meaning | Default |
|---|---|---|
| `FAITHFULIDS_PILOT_N` | explained flows (guide: 100–200) | `80` |
| `FAITHFULIDS_MAX_ROWS` | rows loaded before sampling | `200000` |
| `CIC_DIR` | CICIDS2017 CSV dir (override auto-detect) | auto |
| `HF_TOKEN` | HuggingFace token (Kaggle Secret) | — |

- **Model / precision** are declared in the repo config
  `configs/llms/qwen2_5_3b_instruct.yaml` (Qwen2.5-3B-Instruct, ungated,
  `quantisation: none`/fp16), referenced by
  `experiments/pilot/EXP-PILOT-001_vertical_slice.yaml`. It needs **no HF token**.
  Point the pilot's `llms:` axis at `mistral_7b_instruct_4bit` (gated, needs a
  token) or any other config to change model/precision.

## Pilot simplifications (documented, NON-CITABLE)

To load only **one** LLM on Kaggle hardware while keeping the model-family
firewall intact, the pilot runs the **extractor rule-assisted** (no model; its
config already declares `rule_assisted: true`) and B4's **verifier rule-based**
(grounding checks against the SHAP evidence). Data uses **pilot-grade cleaning**
(dedup/NaN/leakage/label), **not** the full Engelen/Lanvin correction pipeline
(the confirmatory path). Pilot outputs live in the `pilot` tier and `pilot` seed
section, **separate from Tier-A**, and must be excluded from confirmatory
analysis. Use pilot numbers only to estimate effect sizes, variance, sample
sizes, LLM-call budget, and cost — never to decide whether to proceed.

The reproduction chain (run manifest → hashed input CSVs → resolved config →
seeds → metrics) is fully intact and verifiable via `tools/audit_manifests.py`
and the read-only results API.
