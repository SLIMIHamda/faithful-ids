# tools/ - the repository audits itself

Not experiment code. `audit_manifests.py`, `lineage_graph.py`, `firewall_check.py`, `prereg_diff.py`, `release_closure.py`, plus small CI helpers. These back the CI gates.

Five are operator tools rather than gates: `reextract_llm_assisted.py` (re-parse an audit batch through the extractor's registered LLM path — needs a GPU, ledger-backed so re-scoring never re-runs the model), `anchor_pin.py` (resolve a generator's pinned revision for the capability anchor, and format the measured row — it refuses a model with no pinned weights, and never substitutes a published score for a missing one), plus: `rescore_run.py` (token-free replay re-score of a completed run under current instruments), `apply_contingency.py` (materialise a class-handling contingency Decision as the bumped taxonomy — prereg amendment 0001), and `build_audit_batch.py` (build the EXP-G-001 extractor-audit materials — blinded items, the annotator UI, the LLM annotator chunks, and the hidden key — deterministically from the frozen gate seed). The first two refuse loudly rather than guess; `apply_contingency.py` re-derives the Decision and will not write if the recorded one does not reproduce.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
