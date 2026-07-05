# experiments/ - the append-only experiment registry

One YAML per experiment composing configs by reference; declares RQ, hypothesis family, gate dependencies, seed-table section, tier. **Append-only:** a change to a run experiment is a NEW entry with `supersedes:`. `ANCHOR.yaml` defines the anchor once; Tier-B references it (a restated anchor that drifts is a classic irreproducibility bug).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
