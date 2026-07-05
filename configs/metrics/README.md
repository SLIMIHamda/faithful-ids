# configs/metrics/ - metric definitions with formula versions

Layer-1 (mention P/R/F1, DSA, ARC, HFR), Layer-2 erasure (primary cond-exp imputation, secondary retrain-ROAR at anchor; k in {1,3,5}), plausibility judge (family not in explainers, validation gate rho>=0.6). Each metric carries a **formula version** (hostile-audit A12).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
