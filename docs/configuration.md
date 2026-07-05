# Configuration philosophy

All scientific parameters live in [`configs/`](../configs). Source code contains
**zero** magic constants, hardcoded paths, model names, thresholds, or seeds. A
missing config key is a **hard error**, never a silent default.

## Registry + resolved snapshot, not "config files + CLI flags"

CLI flags are invisible parameters — the exact failure mode the immutability
principle forbids. The runner accepts exactly one argument (an experiment ID);
everything else is resolved from the registry and **snapshotted** into the run
as `config.resolved.yaml`. The run is reconstructible from that snapshot alone,
even if `configs/` later evolves.

## Schema versioning

Every config family has a JSON Schema in [`configs/schema/`](../configs/schema),
semver'd by filename (`dataset.v1.json`, …). CI job `validate-configs` validates
every config and experiment file against its schema. Schemas:

- forbid absolute paths and drive letters (regex) — hostile-audit A10;
- require the fields that make the firewall checkable (`model_family`);
- carry the schema flags `exploratory` and `llm_dependent`.

## How references resolve

Configs reference other configs, prompts by hash, the KB by version, and seeds
by table section. Reference resolution flattens all of these into a single
`config.resolved.yaml`:

```
experiment  --references-->  dataset/detector/attribution/llm/generator/sampling/metric configs
generator   --references-->  prompt (by name + semver + sha256, verified against prompts/REGISTRY.json)
b4_vte      --references-->  kb (by version + hash, verified against kb/VERSIONS.md)
experiment  --references-->  seed table section
```

Resolution fails loudly if any referenced hash/version does not match the
registry — a drifted prompt or KB can never be silently substituted.

## Schema flags

- `llm_dependent: false` (B0, B1) → the cell-expansion logic yields
  `2 + 3×3 = 11` generator–LLM cells per dataset×detector.
- `exploratory: true` (EXP-X-001) → CI blocks the run from any headline paper
  asset (`mapping-completeness`).

## Pre-registered subtree

[`configs/statistics/`](../configs/statistics) is frozen at tag `prereg-v1`.
Changes after the tag must arrive as append-only files under
`configs/statistics/amendments/`. See
[`registering-experiments.md`](registering-experiments.md) and
[`reproducibility-guide.md`](reproducibility-guide.md).
