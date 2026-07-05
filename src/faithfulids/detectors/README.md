# detectors/ - L2, training/eval artifact boundary

Model definitions + training entrypoints. Training writes frozen artifacts to `models/`; evaluation code loads frozen artifacts ONLY (edge 6: inference paths cannot import training).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
