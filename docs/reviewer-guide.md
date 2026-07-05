# Reviewer guide

Fast recipes for an artifact reviewer. Start in
[`../artifact/reviewer_kit/`](../artifact/reviewer_kit) (the L1 quickstart,
< 30 min). Everything runs inside the pinned container.

## "Verify a headline figure in 10 minutes" (L1)

```bash
make reproduce-l1
git diff --exit-code -- paper/figures/generated paper/tables/generated
```

If the working tree is clean after regeneration, every figure/table byte-matches
the committed asset — the assets are genuinely generated, not hand-drawn.

## "Where does Figure N come from?" (lineage)

```bash
make lineage TARGET=fig_cd_diagram
```

Renders the DAG from the figure down to prompt hashes, KB version, seed table
section, gate run IDs, commit, and container digest. See
[`lineage.md`](lineage.md).

## "Is the firewall real?" (methods claim)

```bash
make firewall            # prompt-hash + model-family disjointness + import scan
make import-contracts    # the layered architecture + forbidden edges
```

Both must pass. See [`firewall.md`](firewall.md).

## "Did they select runs to get the result?" (p-hacking)

Open the relevant `analysis/configs/*.yaml`: it enumerates the **exact** run IDs
(no globs). `paper/mapping.yaml` ties every figure/table/claim to those run IDs,
and `mapping-completeness` guarantees no paper number exists outside that chain
(hostile-audit A7).

## "Are the pre-registered thresholds really pre-registered?"

```bash
make prereg-diff         # diff configs/statistics against tag prereg-v1
```

The OSF DOI in [`../CITATION.cff`](../CITATION.cff) stores the external
timestamp; the tag + freeze CI prevent on-repo drift (A5).

## "The datasets are not redistributed — can I still verify?"

Yes, to L1–L3 without the raw data. For L4, acquire the public datasets and run
`make data DATASET=…`; `data-integrity.yml` verifies the checksum chain (A3).
See [`../REPRODUCING.md`](../REPRODUCING.md).

## What to check for a "Reusable" badge

- `make test` green (instrument correctness, determinism, contracts);
- `make reproduce-l1` reproduces every asset;
- a new dataset/generator can be added by config alone (demonstrated in
  `tests/`), evidencing the extension story in
  [`../REPOSITORY_BLUEPRINT.md`](../REPOSITORY_BLUEPRINT.md) §7.
