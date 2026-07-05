# metrics/ - L4, STRUCTURALLY generator-blind

Receives `(claims, attribution, detector-outputs, erasure-config)` and returns numbers. Function signatures make it impossible to pass generator identity - grouping keys are attached downstream by orchestration. May NOT import `generation` (edge 1).

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
