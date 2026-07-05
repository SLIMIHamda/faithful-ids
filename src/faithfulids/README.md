# src/faithfulids/ - the layered library

Layered (blueprint section 5), import-contract enforced. The library serves the registry, not vice-versa. **May NOT contain:** file paths, dataset/model names, thresholds, prompt text (all from configs), or `utils/`/`common/`/`misc/` modules - every module has a scientific responsibility.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
