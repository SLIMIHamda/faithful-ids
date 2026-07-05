# data/ - raw data is sacred; one-directional flow

Four strata with strictly one-directional flow: `raw -> corrected -> processed -> splits`, plus `cache/`. Payloads DVC-tracked; checksums, split indices, and the LLM ledger in git. **May NOT contain:** code or any human-edited file.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
