# Kaggle pilot launcher

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
