# models/ - frozen trained detector artifacts

One directory per training run: `model.bin` + `MANIFEST.json` (data hash, config hash, seed, env hash, training metrics) + `training_metrics.json`. Naming: `<detector>__<dataset>__seed<NN>/`. **May NOT contain:** models without manifests; overwritten models (new training = new directory).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
