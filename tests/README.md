# tests/ - correctness of the instruments

unit (per module; metrics vs hand-computed fixtures - the RQ0 analogue), metrics_fixtures (worked examples with known values, in git), determinism (same seed -> byte-identical, per stage), contracts (import-layer, firewall, schema round-trips), pipeline_smoke (5-instance end-to-end in CI).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
