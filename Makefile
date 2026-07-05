# The ONLY sanctioned entry points. No experiment is invoked outside a Make
# target, and every target that runs science goes through the orchestration
# layer so that provenance is captured. Targets whose science is not yet
# implemented fail loudly (NotImplementedError) rather than silently no-op.

PY ?= python
EXP ?=
H ?=
DATASET ?=

.DEFAULT_GOAL := help

.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# --------------------------------------------------------------------------- #
# Environment
# --------------------------------------------------------------------------- #
.PHONY: lock
lock:  ## Regenerate the exact hashed dependency lock (uv.lock)
	uv lock

.PHONY: install
install:  ## Create the pinned environment from uv.lock
	uv sync --frozen --extra dev

.PHONY: fingerprint
fingerprint:  ## Emit the environment hash recorded in every run manifest
	$(PY) environment/env-fingerprint.py

# --------------------------------------------------------------------------- #
# Quality gates (these back the CI workflows)
# --------------------------------------------------------------------------- #
.PHONY: test
test:  ## Run the unit / contract / determinism / smoke test suite
	$(PY) -m pytest

.PHONY: lint
lint:  ## Ruff lint
	ruff check src tests tools analysis

.PHONY: typecheck
typecheck:  ## mypy strict on the library
	mypy

.PHONY: validate-configs
validate-configs:  ## Validate every config/experiment file against configs/schema/
	$(PY) -m faithfulids.orchestration.validate_configs

.PHONY: import-contracts
import-contracts:  ## Enforce the layered architecture + forbidden edges
	lint-imports

.PHONY: firewall
firewall:  ## Prompt-hash + model-family disjointness + import scan (circularity firewall)
	$(PY) tools/firewall_check.py

.PHONY: determinism
determinism:  ## Same-seed byte-identical check on the toy pipeline
	$(PY) -m pytest tests/determinism tests/pipeline_smoke -q

# --------------------------------------------------------------------------- #
# Data pipeline (L4)
# --------------------------------------------------------------------------- #
.PHONY: data
data:  ## raw -> corrected -> processed -> splits for DATASET=<id> (checksummed)
	@test -n "$(DATASET)" || (echo "ERROR: set DATASET=<dataset config id>" && exit 2)
	$(PY) -m faithfulids.orchestration.data_pipeline --dataset $(DATASET)

# --------------------------------------------------------------------------- #
# Experiment execution — the runner accepts exactly one argument: an EXP id.
# --------------------------------------------------------------------------- #
.PHONY: run
run:  ## Execute a registered experiment: make run EXP=<experiment id>
	@test -n "$(EXP)" || (echo "ERROR: set EXP=<experiment id>" && exit 2)
	$(PY) -m faithfulids.orchestration.cli run --experiment $(EXP)

# --------------------------------------------------------------------------- #
# Analysis (L2) — pure consumer of runs/**
# --------------------------------------------------------------------------- #
.PHONY: analyse
analyse:  ## Recompute one hypothesis' statistics: make analyse H=<analysis config>
	@test -n "$(H)" || (echo "ERROR: set H=<analysis config name>" && exit 2)
	$(PY) -m analysis.run --config $(H)

.PHONY: analyse-all
analyse-all:  ## Recompute every analysis config
	$(PY) -m analysis.run --all

# --------------------------------------------------------------------------- #
# Paper assets (L1) — regenerated, never hand-edited
# --------------------------------------------------------------------------- #
.PHONY: figures
figures:  ## Regenerate every figure from analysis outputs
	$(PY) -m paper.figures.build

.PHONY: tables
tables:  ## Regenerate every table from analysis outputs
	$(PY) -m paper.tables.build

.PHONY: paper
paper: figures tables  ## Regenerate all paper assets and assemble the manuscript
	$(PY) -m paper.assemble

.PHONY: reproduce-l1
reproduce-l1: figures tables  ## L1: every figure & table from released analysis outputs (<30 min)
	@echo "L1 reproduction complete — diff paper/**/generated against committed hashes."

.PHONY: reproduce-l3
reproduce-l3:  ## L3: recompute metrics from the LLM ledger in cache-only replay mode
	$(PY) -m faithfulids.orchestration.cli replay --tier L3

# --------------------------------------------------------------------------- #
# Repository self-audit (these back the CI gates)
# --------------------------------------------------------------------------- #
.PHONY: audit
audit:  ## Verify every runs/ manifest: hashes, completeness, immutability
	$(PY) tools/audit_manifests.py

.PHONY: lineage
lineage:  ## Render the artifact lineage DAG for a figure/table/claim: make lineage TARGET=...
	$(PY) tools/lineage_graph.py $(TARGET)

.PHONY: prereg-diff
prereg-diff:  ## Diff pre-registered files against tag prereg-v1
	$(PY) tools/prereg_diff.py

.PHONY: release
release:  ## Build + verify the release bundle (no dangling references)
	$(PY) tools/release_closure.py

.PHONY: clean
clean:  ## Remove caches (NEVER touches runs/, data/raw, models/)
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
