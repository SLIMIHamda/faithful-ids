# Pinned base image BY DIGEST. The digest — not the tag — is what a manifest
# records; tags are mutable, digests are not (hostile-audit A10: the artifact is
# authored on one OS and executed in the container on another).
#
# Replace the digest below with the resolved digest for your CUDA/torch target
# and record it in environment/cuda-versions.md. `docker buildx imagetools
# inspect python:3.11-slim-bookworm` yields the current digest.
FROM python@sha256:0000000000000000000000000000000000000000000000000000000000000000
# ^ PLACEHOLDER digest — pin before any L4 run. env-fingerprint.py reads the
#   effective digest from $CONTAINER_IMAGE_DIGEST, set at build time below.

ARG CONTAINER_IMAGE_DIGEST="sha256:0000000000000000000000000000000000000000000000000000000000000000"
ENV CONTAINER_IMAGE_DIGEST=${CONTAINER_IMAGE_DIGEST}

# Deterministic Python + reproducible builds
ENV PYTHONHASHSEED=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    SOURCE_DATE_EPOCH=1700000000

# uv is the ONLY dependency resolver — the environment is created from the exact
# hashed lock, never from loose pip installs.
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
# --frozen refuses to proceed if uv.lock is stale or a placeholder (fail-loud).
RUN uv sync --frozen --no-dev

COPY . .
RUN uv sync --frozen --extra dev

# Determinism flags for torch kernels are set by the runner per stage and
# recorded in the manifest; see docs/reproducibility-guide.md.
ENTRYPOINT ["uv", "run", "--frozen", "make"]
CMD ["help"]
