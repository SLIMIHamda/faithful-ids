# Knowledge-base version history

The KB is a versioned scientific artifact (like a dataset): a retrieval corpus
that silently drifts destroys the reproducibility of B4. Configs reference the KB
by **version + hash**; `kb/VERSIONS.yaml` is the machine-readable registry used
by reference resolution.

| KB name | Version | Date | Notes |
|---|---|---|---|
| feature_semantics | 1.1.0 | 2026-07-17 | CICIDS2017 dictionary expanded 8 → 76 entries: full coverage of the runtime feature vocabulary (the 8-entry corpus left most prompts' "Feature meanings" sections near-empty — found analyzing the first K-way smoke). Original 8 descriptions preserved verbatim. |
| attack_classes | 1.1.0 | 2026-07-17 | Content unchanged; version synced with the `cicids2017` registry key (one key covers both per-dataset KB files). |
| cicids2017 | 1.1.0 | 2026-07-17 | Anchor-dataset KB bump carrying the feature_semantics expansion. |
| feature_semantics | 1.0.0 | 2026-07-04 | Initial per-dataset flow-feature dictionaries. |
| attack_classes | 1.0.0 | 2026-07-04 | Initial per-dataset attack-class descriptions. |
| cicids2017 | 1.0.0 | 2026-07-04 | Feature + attack-class KB for the anchor dataset. |
| unsw_nb15 | 1.0.0 | 2026-07-04 | Feature KB for the Tier-A second dataset. |
| cse_cic_ids2018 | 1.0.0 | 2026-07-04 | Reserved for the Tier-B transfer dataset. |

The optional CTI snapshot used by the single exploratory cell is versioned
separately in `kb/cti/SNAPSHOT.md`.
