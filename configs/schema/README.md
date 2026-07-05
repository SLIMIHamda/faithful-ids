# configs/schema/ - versioned JSON Schemas

One JSON Schema per config family, semver'd (`dataset.v1.json`...). Every config/experiment file is validated against these in CI (`validate-configs`). Schemas forbid absolute paths / drive letters (hostile-audit A10) and enforce firewall flags (model-family fields).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
