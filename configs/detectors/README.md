# configs/detectors/ - detector configs

Per-detector hyperparameters + determinism flags. `xgboost` is the anchor detector (exact TreeSHAP admissible); `ft_transformer` (DeepSHAP, approximate); `random_forest` Tier-B continuity only.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
