# analysis/ - statistics, a pure consumer of runs/**

Imports only `faithfulids.results` + `faithfulids.framework`. Each analysis config enumerates the EXACT run IDs it consumes (no globs - globbing is silent selection bias) and references pre-registered tests/thresholds by config path. Cannot trigger or re-run experiments (edge 4).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
