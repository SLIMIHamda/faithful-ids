# Amendment 0001 — multiclass class-handling contingency (Tier-A)

- **Date:** 2026-07-20
- **Status:** Registered (append-only; this file is never edited after commit)
- **Amends:** the prereg frozen at tag `prereg-v1` (commit `14bb4a9`)
- **Timestamp of record:** the git commit introducing this file, made **before**
  the Tier-A contingency smoke and before any Tier-A data exists
- **Deciders:** project author (ruling) after adversarial cross-review of two
  independently drafted contingency proposals (2026-07-19/20)
- **Related:** [`../decision_thresholds.yaml`](../decision_thresholds.yaml)
  (frozen constants: `detector_macro_f1_min`, `detector_recall_floor`,
  `detector_class_min_support`, `contingency_class_failure_fraction`,
  `contingency_min_attack_classes`),
  [`../../taxonomy/cicids2017.yaml`](../../taxonomy/cicids2017.yaml) (taxonomy
  v1.0.0, the rung-1 vocabulary), `docs/adr/0002-class-handling-contingency.md`

## Problem

The Tier-A primary task is K-way (8 canonical CICIDS2017 classes). The
detector-competence gate demands a per-class recall floor. If one or more attack
classes fail that floor at smoke time, the design needs a **pre-registered,
enumerated, exhaustible** rule for what happens next — otherwise class merging
or exclusion after seeing results is undisclosed flexibility.

## Invariants (ratified, binding at every rung)

1. **BENIGN is never merged and never excluded.**
2. **No floor-lowering.** The recall floor value is frozen; the contingency
   changes the class vocabulary, never the threshold.
3. **`recall_floor_exemptions` is EMPTY for Tier-A.** A failing class is handled
   by this contingency, never exempted.
4. **Merges propagate to the taxonomy config and the attack-class KB before
   primary generation.** The taxonomy file is the single source of truth; the
   5.1b drift guard in validate-configs makes a silent merge structurally
   impossible.
5. **Main-text reporting.** Any merge or exclusion, with its trigger statistics,
   is reported in the paper's main text, not an appendix.
6. **The decision is recorded** in `competence.json` and the run manifest of the
   smoke run that triggered it.

## Gate evaluation set (decoupled — decision of 2026-07-20)

Competence is a property of the **detector**, so the gate is evaluated where it
can be estimated: macro-F1 and the per-class recall floor are computed on the
**held-out competence split** — disjoint from the training set and from the
explained set — whose per-class counts support meaningful confidence intervals.
The explained set's per-class composition is reported alongside. A class with
fewer than `detector_class_min_support` instances in the competence split cannot
be certified and is treated exactly as a class failing its floor. (Registered in
the frozen `decision_thresholds.yaml` entries; the alternative — gating on the
~21-per-class explained set, Wilson 95% half-width ≈ ±0.14 at p=0.8 — cannot
distinguish passing from failing and was rejected.)

## Lineage-derived parent map

**Criterion (ratified):** a parent assignment must derive from the dataset's
**published capture lineage** (its own documentation: capture day, scenario,
tooling), never from detector confusability or flow-feature similarity. Reasoning
from what the detector confuses would let detector performance define the label
space the detector is then graded on — a leak.

Under this criterion the map for CICIDS2017 taxonomy v1.0.0 is:

| Canonical class | Parent | Basis |
|---|---|---|
| FTP-Patator | **Brute Force** | Tuesday brute-force captures, patator tooling — same documented scenario |
| SSH-Patator | **Brute Force** | Tuesday brute-force captures, patator tooling — same documented scenario |
| BENIGN, DoS, DDoS, PortScan, Web Attack, Bot | *itself (no parent)* | no published-lineage sibling |

The only contingency merge available is therefore
**FTP-Patator + SSH-Patator → Brute Force**. DoS variants and the three Web
Attack variants are already folded at the taxonomy's leaf level. A proposed
`DoS + DDoS → Volumetric Flood` merge was **considered and withdrawn**: its
justification ("at flow-feature level both are floods") is a statement about
detector behaviour, not published lineage — in CICIDS2017's own documentation
DoS and DDoS are distinct captures on different days with different tooling
(LOIC for DDoS). It fails the criterion and is not available at any rung.

## Trigger — class-counted, global, one-pass

Evaluated **once**, immediately after the smoke-stage competence gate, over all
canonical **attack** classes (BENIGN excluded from the count):

- A class **fails** iff its competence-split recall is below
  `detector_recall_floor` **or** its competence-split support is below
  `detector_class_min_support`.
- If the failing fraction is **below** `contingency_class_failure_fraction`
  (0.5): resolve in **one pass** — each failing class merges into its lineage
  parent where one exists; a parentless failing class is routed to the exclusion
  rung (subject to rung-3 admissibility). No second evaluation on the same rung;
  no per-class sequential decisions (the one-pass, class-counted form is the
  outer control that prevents salami-slicing).
- If the failing fraction is **at or above** 0.5: the leaf design is not
  salvageable class-by-class; descend the ladder to the next rung.

The contingency **fires at most once per rung transition** and the resolver
refuses to iterate: one gate evaluation per rung, monotone descent, no backtracking.

## The enumerated ladder (4 rungs — decision of 2026-07-20)

1. **Leaf** — the 8 canonical classes of taxonomy v1.0.0.
2. **Parent-merged** — FTP-Patator + SSH-Patator folded to Brute Force
   (7 classes). The only lineage merge available.
3. **Parent-merged minus excluded blind classes** — parentless classes that fail
   their floor are excluded from the task vocabulary; every exclusion is
   reported in the main text. Admissible **only while at least
   `contingency_min_attack_classes` (3) attack classes survive**.
4. **Binary (BENIGN vs ATTACK)** — terminal rung, reported as a **negative
   finding** for the K-way design (the pilot already established the binary
   task is trivially separable and its explanations are not citable evidence).

The ladder is exhaustible by construction: four enumerated states, one gate
evaluation each, no numeric collapse criterion to tune. (A 3-rung ladder without
rung 3 was rejected: a single parentless failing class — Bot bleeding into
BENIGN is the a-priori candidate — would force the terminal binary rung even if
every other class is fine.)

## Resolution is a gate between smoke and primary — not a relabelling

Any merge or exclusion requires **its own detector fit, competence re-evaluation,
and SHAP re-attribution** under the bumped taxonomy before primary generation:

smoke (detector-only, zero LLM tokens) → `resolve()` (one pass) → if changed:
taxonomy version bump + KB realignment + retrain + re-attribution → competence
gate re-evaluated on the new vocabulary (this is the next rung's one evaluation)
→ **primary generation** → gold-set stratified sampling (generators × final
classes) → analysis/discharge.

Existing artifacts are never relabelled to the merged vocabulary.

## Gate-failure clause

When any registered gate fails after generation (e.g. the extractor audit
EXP-G-001), the legal move is: **the instrument iterates, the annotation is
fixed, and every attempt is logged.** The instrument under test may be revised
and re-gated (semver bump + changelog + re-run); the reference annotation /
gold labels are never edited to meet the gate; each attempt's result is recorded
whether it passes or not. Silent retries have no legal status.

## Implementation

The resolver is a pure, deterministic function
(`faithfulids.detectors.contingency.resolve(competence_table, taxonomy,
thresholds) → Decision{rung, merges, exclusions, trigger_stats, rationale}`),
unit-tested offline, reading its constants from the frozen
`decision_thresholds.yaml`. `tools/apply_contingency.py` materialises a Decision
as the bumped taxonomy config so the drift guard, not discipline, enforces
propagation.
