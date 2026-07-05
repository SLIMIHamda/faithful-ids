# prompts/ - prompts are versioned scientific instruments

Immutable, semver'd, hash-addressed prompt texts with a registry (`REGISTRY.json`). Structural separation of generation / extraction / judging trees is the circularity firewall. **May NOT contain:** code, runtime-assembled f-strings outside registered files, or unfrozen drafts (drafts live in `notebooks/`).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
