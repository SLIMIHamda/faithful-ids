# Naming conventions

Stable IDs are load-bearing: they appear in manifests, the traceability matrix,
and the paper. Never rename an ID that has been run — supersede instead.

## Experiments

```
EXP-<TIER>-<NNN>[_<slug>]
```

| Tier code | Meaning | Example |
|---|---|---|
| `G` | gate | `EXP-G-001_extractor_audit` |
| `A` | Tier A core factorial | `EXP-A-001_core_factorial` |
| `B` | Tier B anchored extension | `EXP-B-002_quantisation` |
| `S` | stochasticity | `EXP-S-001_generation_variance` |
| `H` | human study | `EXP-H-001_triage_study` |
| `X` | exploratory | `EXP-X-001_cti_rag_anchor` |
| `TOY` | toy/smoke (CI only, never cited) | `EXP-TOY-001` |

## Runs

```
<EXP-ID>__<git-sha7>__<UTC-ISO>
e.g. EXP-A-001__a1b2c3d__2026-08-12T0930Z
```

The run ID embeds the commit and UTC start, so it is unique and self-dating.
Re-execution mints a new run ID; a run ID is never reused.

## Prompts

```
prompts/<tree>/<name>/v<MAJOR>.<MINOR>.<PATCH>.md
```

Registered in `prompts/REGISTRY.json` as `name → semver → sha256 → frozen`.
Referenced from configs by name + semver; the sha256 is verified at run time.

## Knowledge base

Referenced by `version` + `hash`; history in `kb/VERSIONS.md`. The CTI snapshot
carries a date in `kb/cti/SNAPSHOT.md`.

## Datasets / detectors / models

- Dataset config IDs: `cicids2017_corrected`, `cicids2017_raw`, `unsw_nb15`,
  `cse_cic_ids2018`.
- Model artifact directories: `<detector>__<dataset>__seed<NN>/`, e.g.
  `xgboost__cicids2017c__seed42/`.

## Analysis outputs

```
<analysis-config>__<git-sha7>__<date>/
e.g. h1_gap__r4e5f6a__2026-09-02/
```

## Figures / tables

`fig_<slug>` / `tab_<slug>`; spec, script, and generated asset share the slug:
`paper/figures/specs/fig_cd_diagram.yaml`,
`paper/figures/src/fig_cd_diagram.py`,
`paper/figures/generated/fig_cd_diagram.pdf`.

## Hypothesis families

`H0, H1, H2, H3, H-T, H4` — memberships for Holm–Bonferroni live in
`configs/statistics/hypothesis_families.yaml`.
