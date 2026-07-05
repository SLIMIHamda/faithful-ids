# runs/ - WRITE-ONCE run ledger

Every execution writes an immutable, hash-manifested run directory (`MANIFEST.json`, `config.resolved.yaml`, `STATUS`, `artifacts/`, `logs/`). **Never** modified, deleted, hand-edited, or 'cleaned'. Failed runs keep `STATUS=FAILED` forever - negative provenance is provenance. Payloads DVC-tracked; manifests in git.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
