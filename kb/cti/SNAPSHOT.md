# CTI snapshot (exploratory cell only)

CTI drifts; a snapshot does not. The single exploratory ablation cell
(`EXP-X-001` CTI-RAG at the anchor) retrieves from a **frozen** copy of an
ATT&CK / CTI corpus, pinned by date and hash so the exploratory result is
reproducible even as the upstream feeds change.

| Field | Value |
|---|---|
| Corpus | MITRE ATT&CK (Enterprise) + curated IDS CTI notes |
| Snapshot date | 2026-07-04 |
| Snapshot version | 0.1.0 (exploratory) |
| Content hash | pin-pending (compute over the frozen corpus at acquisition) |
| License | Upstream ATT&CK / CTI terms — see LICENSE-ARTIFACTS.md |

This corpus is used **only** by `EXP-X-001`, which is schema-flagged
`exploratory: true`; CI (`mapping-completeness`) blocks any headline figure or
table from citing it.
