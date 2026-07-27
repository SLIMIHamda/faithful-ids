# tools/ - the repository audits itself

Not experiment code. `audit_manifests.py`, `lineage_graph.py`, `firewall_check.py`, `prereg_diff.py`, `release_closure.py`, plus small CI helpers. These back the CI gates.

Two are operator tools rather than gates: `rescore_run.py` (token-free replay re-score of a completed run under current instruments) and `apply_contingency.py` (materialise a class-handling contingency Decision as the bumped taxonomy — prereg amendment 0001). Both refuse loudly rather than guess; `apply_contingency.py` re-derives the Decision and will not write if the recorded one does not reproduce.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
