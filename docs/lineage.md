# Artifact lineage & the manifest schema

**Universal rule.** Every artifact directory — dataset stratum, model, cache
entry, run, analysis output, generated figure — carries a `MANIFEST.json`
conforming to `src/faithfulids/provenance/manifest.v1.json`.

## Manifest fields (blueprint §6)

```
identity      : artifact ID, type, schema version
producer      : experiment ID (if any), pipeline stage, code version =
                git commit + dirty-flag (dirty runs REFUSED outside debug mode,
                which stamps NON-CITABLE)
configuration : resolved-config snapshot hash (+ the snapshot itself for runs)
inputs        : list of {artifact ID, content hash} for EVERY input —
                datasets, splits, models, KB version, prompt hashes,
                gate run IDs, upstream caches
environment   : lock-file hash, container image digest, hardware
                (GPU model, driver, cuDNN), OS
randomness    : every seed consumed, keyed by stage and cell (from the seed table)
models        : detector artifact hashes; LLM identities
                {weights sha / API snapshot ID, quantisation, revision};
                extractor & judge identities likewise
timestamps    : start/end UTC
outputs       : file list with sha256 each
status        : COMPLETE | FAILED  (terminal, immutable)
```

## Lineage closure

Because every manifest's `inputs` are `(ID, hash)` pairs, `tools/lineage_graph.py`
reconstructs the full DAG behind any paper asset:

```
Figure 4
  → analysis h1_gap
    → runs [EXP-A-001__…]
      → splits → corrected → raw checksums
      → models → training runs
      → prompts vX @hash
      → KB vY @hash
      → extractor-audit gate run
      → seed table §
      → commit
      → container digest
```

This is the mechanical answer to every "which …?" question in Principle 2
(which config? model? seed? split? commit? prompts? verifier? extraction model?
metrics? statistics?).

## Instruments tracked as versioned inputs

Prompt versions (registry hash), KB version, correction-pipeline version,
erasure-operator config (operator type + **imputation-model fit hash** — the
fitted imputation model is itself a manifested cache artifact), corruption-
operator config with per-instance ground-truth labels, judge identity + its
validation-run reference, and the human-study materials build.

## No silent regeneration

Cache lookups are by content-address of **all** inputs; a hash miss creates a
*new* entry, and the consumer's manifest records which entry it used. A changed
input never overwrites — it forks a new key (hostile-audit A6, A11).
