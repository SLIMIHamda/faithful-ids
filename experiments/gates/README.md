# experiments/gates/ - gate experiments (hard dependencies)

EXP-G-001 extractor audit (gate F1>=0.95) and EXP-G-002 RQ0 calibration (gate sens/spec>=0.9). Their passing run IDs are mandatory references for downstream experiments.

`EXP-G-001_audit_record/` holds the **interim** blind human audit (150-item, single-annotator, directional-agreement) that resolved the B4 "DSA regression" as an extractor artifact and validated the `1.1.0→1.4.0` repairs — see its [`AUDIT_RECORD.md`](EXP-G-001_audit_record/AUDIT_RECORD.md). It is evidence/provenance, **not** a gate pass: EXP-G-001 stays `registered` until the formal 300-item, dual-annotated, adjudicated run against extractor 1.4.0.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
