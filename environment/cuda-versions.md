# CUDA / cuDNN / torch determinism notes

Every run manifest records the container image **digest**, GPU model, driver,
CUDA, and cuDNN versions (see `env-fingerprint.py`). This file is the human
record of *why* those pins were chosen and which artifacts are byte-identical
vs. tolerance-bounded on GPU.

## Pinned versions (fill in at container build)

| Component | Pinned value | Source of pin |
|---|---|---|
| Base image | `python@sha256:…` (placeholder) | `docker buildx imagetools inspect` |
| CUDA toolkit | e.g. `12.1` | matched to torch wheel |
| cuDNN | e.g. `8.9.x` | matched to CUDA |
| torch | `2.5.1` | `pyproject.toml` |
| NVIDIA driver | recorded per run | `$GPU_DRIVER_VERSION` |

> Replace the placeholder digests in `Dockerfile` and `apptainer.def` with the
> resolved digest and record it here before any L4 (GPU) run.

## Determinism policy (hostile-audit A2)

Temperature 0 is **not** determinism and GPU kernels are not bit-stable. The
scientific answer is the stochasticity protocol (k=3 generations, variance
components as random effects). The engineering answer is recorded per stage:

- `torch.use_deterministic_algorithms(True)` where a stage claims byte-identity.
- `CUBLAS_WORKSPACE_CONFIG=:4096:8` for deterministic cuBLAS.
- `torch.backends.cudnn.deterministic = True`, `benchmark = False`.

These flags, when set, are recorded in the run manifest so a reviewer can see
which stages ran under deterministic kernels.

## Byte-identical vs. tolerance-bounded on GPU

- **Byte-identical:** TreeSHAP from frozen tree models on **CPU**; all
  statistics; all figures/tables.
- **Tolerance-bounded:** DeepSHAP on GPU (FT-Transformer), open-weights LLM
  generations. Tolerances are stated per artifact in
  `docs/reproducibility-guide.md`.
