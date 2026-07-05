# Registering experiments

> propose → schema-validate → register → tag → run

An experiment exists **iff** it has a registered, schema-validated YAML in
[`experiments/`](../experiments). Nothing runs without a registry entry.

## 1. Propose

Write `experiments/<tier>/EXP-<ID>_<slug>.yaml` composing configs **by
reference** (never by restating parameters). Declare:

- `research_question` and `hypothesis_family` (one of H0, H1, H2, H3, H-T, H4);
- `gate_dependencies` (the extractor-audit and RQ0-calibration run IDs it
  requires — for Stage 3+ experiments);
- `seed_table_section`;
- `tier` (gate / tier_a / tier_b / stochasticity / human_study / exploratory);
- schema flags (`exploratory`, and per-generator `llm_dependent`).

Tier B entries reference [`experiments/ANCHOR.yaml`](../experiments) rather than
restating the anchor — a restated anchor that drifts is a classic
irreproducibility bug.

## 2. Schema-validate

```bash
make validate-configs
```

Every experiment YAML is validated against `configs/schema/experiment.v1.json`.
A missing required key fails the PR.

## 3. Register

Open a PR. It triggers `validate-configs` and `mapping-completeness`. **Merge =
registration.** The registry entry is now immutable.

## 4. Amend (never edit)

A change to a run experiment is a **new** entry with a `supersedes:` field
pointing at the old ID. The old entry and its runs remain, labelled. `REGISTRY.md`
is append-only; the paper's appendix auto-lists every registered experiment with
status, so nothing can be quietly dropped (hostile-audit A7).

## 5. Tag (pre-registration)

Before Tier A runs, the statistical protocol
([`configs/statistics/`](../configs/statistics)) and the human-study analysis
plan are committed and tagged `prereg-v1`. The OSF preregistration stores the
hash of the `configs/statistics/` tree at that tag (external timestamp + DOI).
`prereg-freeze.yml` prevents drift thereafter.

## 6. Run

```bash
make run EXP=EXP-A-001
```

The runner refuses a dirty worktree, verifies gate references are PASSED, mints a
run ID, and writes a write-once run directory. See
[`experiment-lifecycle.md`](experiment-lifecycle.md).
