# Per-Artifact Licensing

The MIT license in `LICENSE` covers **source code only**. The scientific
artifacts in this repository are versioned instruments and carry their own
terms. This file is the authoritative per-artifact license map; the release
bundle (`artifact/AVAILABILITY.md`) cross-references it.

| Artifact class | Location | License | Notes |
|---|---|---|---|
| Source code | `src/`, `tools/`, `analysis/src/`, `paper/figures/src/`, `paper/tables/src/` | MIT | see `LICENSE` |
| Prompts (scientific instruments) | `prompts/**` | CC BY 4.0 | frozen, hash-addressed; cite the paper |
| Knowledge base (feature semantics, attack classes) | `kb/feature_semantics/**`, `kb/attack_classes/**` | CC BY 4.0 | versioned; see `kb/VERSIONS.md` |
| CTI snapshot | `kb/cti/**` | Upstream ATT&CK / CTI terms | snapshot only; see `kb/cti/SNAPSHOT.md` |
| Configs & schemas | `configs/**` | MIT | parameters, not results |
| Human-study instruments | `human_study/instruments/**` | CC BY 4.0 | no identifiable data |
| Human-study de-identified data | `human_study/data/raw_deidentified/**` | CC BY-NC 4.0 or IRB-restricted | release only where IRB permits |
| Synthetic sample | `human_study/synthetic_sample/**` | CC0 | fabricated, schema-matching, non-scientific |
| Generated explanations / claims / metrics | `runs/**/artifacts/**` | CC BY 4.0 | derived data; cite the paper |
| Figures & tables | `paper/**/generated/**` | CC BY 4.0 | regenerated from analysis outputs |

## Datasets are NOT redistributed

CICIDS2017, UNSW-NB15, and CSE-CIC-IDS2018 are governed by their original
providers' terms and are **not** redistributed here. `data/raw/**` holds only
checksums and pointers. Acquisition instructions are in `REPRODUCING.md` and
`artifact/AVAILABILITY.md`. The deterministic correction pipeline
(`src/faithfulids/datasets/corrections/`) and row-level split indices
(`data/splits/**/split_manifest.json`) let a reviewer reconstruct the corrected
corpus from the public originals without us redistributing anything.
