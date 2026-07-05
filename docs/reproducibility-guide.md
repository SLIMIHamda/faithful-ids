# Reproducibility guide

The four reproduction tiers and the tolerance policy. The reviewer-facing
command list is in [`../REPRODUCING.md`](../REPRODUCING.md); this document is the
policy behind it.

## Tiers

| Tier | Reproduces | From | Needs | Time |
|---|---|---|---|---|
| L1 | Every figure & table | released `analysis/outputs/` | container, CPU | < 30 min |
| L2 | Every statistic | released `runs/` artifacts | container, CPU | hours |
| L3 | Every metric from explanations | released caches + LLM ledger (replay) | container, CPU | hours |
| L4 | Everything from raw data | public datasets + open weights + API | GPU, API keys | days |

CI continuously exercises **L1** and an **L3 smoke slice**.

## Tolerance policy (hostile-audit A2)

Reproducibility is a disclosed, tested boundary — not a claim of universal
bit-stability.

### Must be byte-identical (CI-enforced)

- frozen splits (`data/splits/**`);
- TreeSHAP attributions from frozen **tree** models on **CPU**;
- all statistics (`analysis/outputs/**`);
- all figures & tables (`paper/**/generated/**`);
- the toy pipeline's metrics (`determinism-smoke`).

### Tolerance-bounded (documented per artifact)

| Artifact | Source of non-determinism | Tolerance |
|---|---|---|
| DeepSHAP (FT-Transformer) | GPU kernels | relative L2 ≤ 1e-3 on attribution vectors |
| Open-weights LLM generations | sampling, GPU | handled by the k=3 stochasticity protocol; variance reported |
| Frontier-API generations | model drift | **replay-verifiable** only (LLM ledger), not re-executable |

### Determinism flags

When a stage claims byte-identity on GPU it records, in its manifest:
`torch.use_deterministic_algorithms(True)`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`,
`cudnn.deterministic=True`, `cudnn.benchmark=False`. See
[`../environment/cuda-versions.md`](../environment/cuda-versions.md).

## Replay-verifiable vs re-executable

The paper's reproducibility statement labels each number:

- **re-executable** — open-weights + frozen models; reproducible within
  tolerance from raw data (L4);
- **replay-verifiable** — frontier-API numbers; reproducible from the
  append-only LLM ledger (L3) but not re-executable because the API model is
  pinned by snapshot ID and may be deprecated.

## What "no silent regeneration" means in practice (A12)

A metric bug found after Tier A ran is fixed as: new **formula version** + new
runs + a **superseding** registry entry + a `CHANGELOG.md` entry. Old runs
remain, labelled; the paper cites only current-version runs; the correction
trail is public.
