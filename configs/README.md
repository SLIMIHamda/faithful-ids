# configs/ - the single source of scientific parameters

ALL parameters live here. Source code contains zero magic constants. Defines the *space* of admissible experiments and encodes pre-registered statistical commitments. **May contain:** YAML configs, JSON Schemas, the seed table, prereg amendments. **May NOT contain:** code, results, machine paths, or defaults duplicated from code - a missing config key is a hard error, never silently defaulted.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
