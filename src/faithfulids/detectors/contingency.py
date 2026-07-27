"""Pre-registered class-handling contingency (L2) — the enumerated ladder.

When a canonical class fails the competence gate, what the design does next is
**pre-registered**, not chosen after seeing results: prereg amendment 0001
(``configs/statistics/amendments/0001-multiclass-class-handling-contingency.md``).
This module is that rule as a pure function.

The properties that make it auditable, and that the tests pin:

* **Deterministic and side-effect free.** ``resolve`` reads a competence table, a
  taxonomy and the frozen thresholds, and returns a ``Decision``. It trains
  nothing, writes nothing, and consults no run state — so it is fully testable
  offline (no sklearn/xgboost/pandas import anywhere in this module).
* **One gate evaluation per rung.** ``resolve`` descends at most one rung per
  call. It cannot look ahead to a rung whose detector has not been fitted and
  gated yet, because that detector's competence table does not exist.
* **Class-counted, global, one pass.** The trigger counts *classes*, not errors,
  over all canonical attack classes at once. Resolving failures one at a time
  would be salami-slicing: each individual merge looks locally justified while
  the design silently walks to binary.
* **Monotone.** The ladder only descends; there is no move back up, and rung 4 is
  terminal (the negative finding stands — it is a result, not a failure state).

Resolution is a **gate between smoke and primary**: a Decision that changes the
vocabulary requires its own detector fit, competence re-evaluation and SHAP
re-attribution before generation. Nothing here relabels an existing artifact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

#: The class that is never merged and never excluded (amendment 0001, invariant 1).
BENIGN_CLASS = "BENIGN"

#: The enumerated ladder. Exhaustible by construction — four states, one gate
#: evaluation each. A numeric collapse criterion ("< 4 classes remaining") was
#: rejected: it is not auditable in the way an enumeration is.
RUNG_LEAF = 1
RUNG_PARENT_MERGED = 2
RUNG_EXCLUDED = 3
RUNG_BINARY = 4
RUNG_NAMES = {
    RUNG_LEAF: "leaf",
    RUNG_PARENT_MERGED: "parent_merged",
    RUNG_EXCLUDED: "parent_merged_minus_excluded",
    RUNG_BINARY: "binary_terminal",
}


class ContingencyExhausted(RuntimeError):
    """Raised when the ladder has no rung left below the current one.

    Reaching this means the terminal binary rung itself failed its gate: the
    detector cannot separate attack from benign on this data, which is a
    detector/data finding and not something a class vocabulary can repair.
    """


@dataclass(frozen=True)
class Decision:
    """The outcome of ONE contingency evaluation."""

    rung: int
    rung_name: str
    changed: bool                               # does the vocabulary change?
    terminal: bool                              # is this the last rung?
    vocabulary: tuple[str, ...]                 # classes AFTER applying this decision
    merges: Mapping[str, str] = field(default_factory=dict)   # class -> new parent
    exclusions: tuple[str, ...] = ()
    failing: tuple[str, ...] = ()               # attack classes that failed the gate
    detector_defect: bool = False               # gate failed for a non-class reason
    trigger_stats: Mapping[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def as_record(self) -> dict[str, Any]:
        """JSON-safe record for ``competence.json`` / the run manifest."""
        return {
            "rung": self.rung,
            "rung_name": self.rung_name,
            "changed": self.changed,
            "terminal": self.terminal,
            "vocabulary": list(self.vocabulary),
            "merges": dict(self.merges),
            "exclusions": list(self.exclusions),
            "failing": list(self.failing),
            "detector_defect": self.detector_defect,
            "trigger_stats": dict(self.trigger_stats),
            "rationale": self.rationale,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "Decision":
        """Rebuild a Decision from :meth:`as_record` — the inverse, so a decision
        recorded on a run can be re-read and acted on without re-deriving it."""
        return cls(
            rung=int(record["rung"]),
            rung_name=str(record["rung_name"]),
            changed=bool(record["changed"]),
            terminal=bool(record["terminal"]),
            vocabulary=tuple(record["vocabulary"]),
            merges=dict(record.get("merges") or {}),
            exclusions=tuple(record.get("exclusions") or ()),
            failing=tuple(record.get("failing") or ()),
            detector_defect=bool(record.get("detector_defect", False)),
            trigger_stats=dict(record.get("trigger_stats") or {}),
            rationale=str(record.get("rationale", "")),
        )


def _support(row: Mapping[str, Any]) -> int:
    """Per-class count under either table shape (binary ``support`` / K-way ``n``)."""
    return int(row.get("support", row.get("n")) or 0)


def failing_classes(
    table: Mapping[str, Any],
    attack_classes: tuple[str, ...],
    *,
    recall_floor: float,
    min_support: int,
) -> tuple[tuple[str, ...], dict[str, dict[str, Any]]]:
    """Attack classes that the competence split does not certify, with the reason.

    Two ways to fail, both blocking: recall below the floor (a real blind spot),
    and support below the minimum (an interval too wide to *demonstrate* the
    floor either way). The second is not a detector defect — it is a class the
    evidence cannot speak about, which is exactly why it must route through the
    contingency instead of being averaged away.

    Iteration is over ``attack_classes`` — the vocabulary being certified — not
    over the table's own keys. A class the competence split does not contain at
    all has n=0, which is below any minimum support, so it fails here rather than
    vanishing from both the numerator and the denominator of the trigger.
    """
    failing: list[str] = []
    reasons: dict[str, dict[str, Any]] = {}
    for cls in attack_classes:
        row = table["per_family"].get(cls) or {}
        recall, n = row.get("detection_recall"), _support(row)
        under = n < min_support
        below = recall is None or float(recall) < recall_floor
        if under or below:
            failing.append(cls)
            reasons[cls] = {
                "detection_recall": None if recall is None else float(recall),
                "n": n,
                "below_floor": bool(below),
                "under_support": bool(under),
                "absent_from_evaluation_set": not row,
            }
    return tuple(sorted(failing)), reasons


def _merge_groups(failing: tuple[str, ...], parents: Mapping[str, str]) -> dict[str, str]:
    """Whole lineage groups to merge, given which classes failed.

    A failing class merges into its parent together with **all its siblings** —
    never alone. Merging one member of a documented group and leaving the others
    beside it would produce a parent class holding a single child, which is a
    rename of that child rather than a merge (and the taxonomy guard rejects the
    resulting map). The unit of this rule is the lineage group.
    """
    merges: dict[str, str] = {}
    for cls in failing:
        parent = parents.get(cls, cls)
        if parent == cls:
            continue  # parentless — the exclusion rung handles it
        for sibling, sib_parent in parents.items():
            if sib_parent == parent:
                merges[sibling] = parent
    return merges


def _vocabulary(
    classes: tuple[str, ...], merges: Mapping[str, str], exclusions: tuple[str, ...]
) -> tuple[str, ...]:
    out: list[str] = []
    for cls in classes:
        if cls in exclusions:
            continue
        name = merges.get(cls, cls)
        if name not in out:
            out.append(name)
    return tuple(out)


def resolve(
    competence_table: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
    thresholds: Mapping[str, float],
    *,
    current_rung: int = RUNG_LEAF,
    vocabulary: tuple[str, ...] | None = None,
) -> Decision:
    """Apply the pre-registered contingency to ONE competence evaluation.

    ``thresholds`` carries the frozen prereg values: ``recall_floor``,
    ``min_support``, ``class_failure_fraction`` and ``min_attack_classes``.
    ``current_rung`` is the rung the evaluated detector was fitted at, so the
    result is always a legal one-step descent from a rung that actually has data.

    ``vocabulary`` is the class set actually being certified — the classes the
    evaluated detector was fitted on. It defaults to the taxonomy's canonical
    classes, which is the Tier-A case (every canonical class present). Passing
    the fitted vocabulary matters when a run's data does not cover the whole
    taxonomy: the trigger is then a statement about the task that was really run,
    and the canonical classes missing from the fit are recorded in
    ``trigger_stats['absent_from_fit']`` rather than quietly dropping out of both
    sides of the fraction.
    """
    if current_rung >= RUNG_BINARY:
        raise ContingencyExhausted(
            "the terminal binary rung failed its own competence gate: no class "
            "vocabulary can repair a detector that cannot separate attack from "
            "benign. Report the negative finding (amendment 0001, rung 4)."
        )
    canonical = tuple(taxonomy["canonical_classes"])
    classes = tuple(vocabulary) if vocabulary is not None else canonical
    parents = dict(taxonomy["parents"])
    recall_floor = float(thresholds["recall_floor"])
    min_support = int(thresholds["min_support"])
    fraction = float(thresholds["class_failure_fraction"])
    min_attack = int(thresholds["min_attack_classes"])

    attack_classes = tuple(c for c in classes if c != BENIGN_CLASS)
    failing, reasons = failing_classes(
        competence_table, attack_classes,
        recall_floor=recall_floor, min_support=min_support,
    )
    n_attack = len(attack_classes)
    failing_fraction = (len(failing) / n_attack) if n_attack else 0.0
    stats: dict[str, Any] = {
        "evaluated_at_rung": current_rung,
        "vocabulary": list(classes),
        "absent_from_fit": [c for c in canonical if c not in set(classes)],
        "n_attack_classes": n_attack,
        "n_failing": len(failing),
        "failing_fraction": failing_fraction,
        "class_failure_fraction_threshold": fraction,
        "recall_floor": recall_floor,
        "min_support": min_support,
        "macro_f1": float(competence_table["macro_f1"]),
        "reasons": reasons,
        "one_pass": True,
    }

    if not failing:
        # The class vocabulary is fine. A macro-F1 failure here is a DETECTOR
        # problem (or a benign-side problem) and must not be laundered into a
        # merge: no class merge is licensed by "the model is generally weak".
        defect = float(competence_table["macro_f1"]) < float(
            thresholds.get("macro_f1_min", 0.0)
        )
        return Decision(
            rung=current_rung,
            rung_name=RUNG_NAMES[current_rung],
            changed=False,
            terminal=current_rung == RUNG_BINARY,
            vocabulary=classes,
            failing=(),
            detector_defect=defect,
            trigger_stats=stats,
            rationale=(
                "Every canonical attack class is certified on the competence split; "
                "the registered vocabulary stands."
                if not defect else
                "No class fails the recall floor, but macro-F1 is below its minimum: "
                "this is a detector defect, not a class-vocabulary problem, and the "
                "contingency licenses no merge for it."
            ),
        )

    if failing_fraction >= fraction:
        # Not salvageable class-by-class. Descend one rung and re-gate there —
        # this is the outer control that stops a run of individually reasonable
        # merges from walking the design to binary unnoticed.
        if current_rung == RUNG_LEAF:
            merges = _merge_groups(tuple(parents), parents)  # every available fold
            vocab = _vocabulary(classes, merges, ())
            return Decision(
                rung=RUNG_PARENT_MERGED,
                rung_name=RUNG_NAMES[RUNG_PARENT_MERGED],
                changed=bool(merges),
                terminal=False,
                vocabulary=vocab,
                merges=merges,
                failing=failing,
                trigger_stats=stats,
                rationale=(
                    f"{len(failing)}/{n_attack} attack classes fail the competence gate "
                    f"({failing_fraction:.0%} >= {fraction:.0%}): the leaf vocabulary is not "
                    f"salvageable class-by-class, so the design descends to the parent-merged "
                    f"rung and is re-gated there. Failing: {', '.join(failing)}."
                ),
            )
        # Already merged and still failing at scale -> terminal binary.
        return _binary(classes, failing, stats, n_attack, failing_fraction, fraction)

    # --- below the trigger: resolve every failing class in ONE pass --------- #
    merges = _merge_groups(failing, parents)
    exclusions = tuple(c for c in failing if parents.get(c, c) == c)
    if BENIGN_CLASS in exclusions or BENIGN_CLASS in merges:
        raise AssertionError(f"{BENIGN_CLASS} can never be merged or excluded")

    if not exclusions:
        vocab = _vocabulary(classes, merges, ())
        return Decision(
            rung=RUNG_PARENT_MERGED,
            rung_name=RUNG_NAMES[RUNG_PARENT_MERGED],
            changed=True,
            terminal=False,
            vocabulary=vocab,
            merges=merges,
            failing=failing,
            trigger_stats=stats,
            rationale=(
                f"{len(failing)}/{n_attack} attack classes fail ({failing_fraction:.0%} < "
                f"{fraction:.0%}), each with a documented lineage parent: one pass folds "
                f"{', '.join(sorted(merges))} into {', '.join(sorted(set(merges.values())))}. "
                f"Failing: {', '.join(failing)}."
            ),
        )

    # Parentless failures need the exclusion rung, which is admissible only while
    # enough attack classes survive to keep the K-way claim meaningful.
    vocab = _vocabulary(classes, merges, exclusions)
    surviving_attacks = tuple(c for c in vocab if c != BENIGN_CLASS)
    if len(surviving_attacks) < min_attack:
        return _binary(classes, failing, stats, n_attack, failing_fraction, fraction,
                       extra=(f"excluding {', '.join(exclusions)} would leave "
                              f"{len(surviving_attacks)} attack class(es), below the "
                              f"registered minimum of {min_attack}"))
    return Decision(
        rung=RUNG_EXCLUDED,
        rung_name=RUNG_NAMES[RUNG_EXCLUDED],
        changed=True,
        terminal=False,
        vocabulary=vocab,
        merges=merges,
        exclusions=exclusions,
        failing=failing,
        trigger_stats=stats,
        rationale=(
            f"{len(failing)}/{n_attack} attack classes fail ({failing_fraction:.0%} < "
            f"{fraction:.0%}). One pass: "
            + (f"{', '.join(sorted(merges))} fold into "
               f"{', '.join(sorted(set(merges.values())))}; " if merges else "")
            + f"{', '.join(exclusions)} have no documented lineage parent and are excluded "
              f"from the task vocabulary (reported in the main text). "
              f"{len(surviving_attacks)} attack classes survive (minimum {min_attack})."
        ),
    )


#: The label_map sentinel for a raw label that is not part of the task vocabulary.
EXCLUDED = "excluded"


def apply_to_taxonomy(
    taxonomy: Mapping[str, Any], decision: Decision, *, new_version: str
) -> dict[str, Any]:
    """Materialise a ``Decision`` as the next class taxonomy. PURE — returns a new
    dict and touches no file (``tools/apply_contingency.py`` does the I/O).

    This is the step that makes the contingency mechanical rather than
    disciplinary: the vocabulary the next detector is fitted on comes from the
    Decision, so the config drift guard — not anybody's memory — enforces that a
    resolved gate failure actually propagates to the taxonomy, the KB, and the
    fit.

    Three transformations, in the order the taxonomy's own invariants require:

    * **canonical_classes** — excluded classes drop out; a merged group collapses
      to its parent name at the position of the group's first member, so class
      order stays stable for anyone diffing the file.
    * **label_map** — every raw label pointing at an excluded class is retargeted
      to ``"excluded"``; every label pointing at a merged class is retargeted to
      the parent. Labels already excluded stay excluded. The map keeps its full
      key set: a raw label is never dropped, because a dropped key would make the
      loader silently ignore rows instead of visibly excluding them.
    * **parents** — the lineage map is a standing fact about the dataset, not a
      log of what has been applied, so surviving classes KEEP their recorded
      parent and a future rung can still use it. Two exceptions: a merge parent
      that is now itself canonical becomes its own parent, and a lineage group
      that an exclusion has reduced to a single survivor is dissolved (a lone
      child cannot merge with itself, and ``validate-configs`` rejects a
      non-canonical parent with fewer than two children).

    Raises ``ValueError`` for a decision there is nothing to materialise: one that
    changes no vocabulary, and the terminal binary rung — rung 4 is a **negative
    finding to report**, not a class taxonomy to fit (the binary path does not
    read this file at all).
    """
    if not decision.changed:
        raise ValueError(
            f"decision at rung {decision.rung} ({decision.rung_name}) changes no "
            "vocabulary — there is nothing to materialise"
        )
    if decision.rung == RUNG_BINARY:
        raise ValueError(
            "rung 4 is the terminal binary rung: a NEGATIVE FINDING for the "
            "multi-class design, reported in the main text. It is not a class "
            "taxonomy — the binary path does not read this config."
        )

    merges = dict(decision.merges)
    exclusions = set(decision.exclusions)
    if BENIGN_CLASS in exclusions or BENIGN_CLASS in merges:
        raise AssertionError(f"{BENIGN_CLASS} can never be merged or excluded")

    canonical = list(taxonomy["canonical_classes"])
    unknown = (exclusions | set(merges)) - set(canonical)
    if unknown:
        raise ValueError(
            f"decision names {sorted(unknown)}, which are not canonical classes of "
            f"taxonomy {taxonomy.get('id')!r} v{taxonomy.get('version')} — the decision "
            "was resolved against a different taxonomy version"
        )

    new_canonical: list[str] = []
    for cls in canonical:
        if cls in exclusions:
            continue
        name = merges.get(cls, cls)
        if name not in new_canonical:
            new_canonical.append(name)

    missing = set(decision.vocabulary) - set(new_canonical)
    if missing:
        raise ValueError(
            f"applying the decision would drop {sorted(missing)}, which its own "
            "surviving vocabulary contains — refusing to write an inconsistent taxonomy"
        )

    new_label_map: dict[str, str] = {}
    for raw, target in taxonomy["label_map"].items():
        if target == EXCLUDED or target in exclusions:
            new_label_map[raw] = EXCLUDED
        else:
            new_label_map[raw] = merges.get(target, target)

    old_parents = dict(taxonomy["parents"])
    survivors: dict[str, list[str]] = {}
    for cls in new_canonical:
        survivors.setdefault(old_parents.get(cls, cls), []).append(cls)
    new_parents: dict[str, str] = {}
    for cls in new_canonical:
        parent = old_parents.get(cls, cls)
        # own parent when: untouched leaf, or a merge parent now canonical, or the
        # sole survivor of a group an exclusion broke
        new_parents[cls] = parent if len(survivors.get(parent, ())) >= 2 else cls

    out = dict(taxonomy)
    out["version"] = new_version
    out["canonical_classes"] = new_canonical
    out["label_map"] = new_label_map
    out["parents"] = new_parents
    return out


def _binary(
    classes: tuple[str, ...],
    failing: tuple[str, ...],
    stats: dict[str, Any],
    n_attack: int,
    failing_fraction: float,
    fraction: float,
    *,
    extra: str = "",
) -> Decision:
    """The terminal rung: BENIGN vs ATTACK, reported as a negative finding.

    Not an error path. The pilot already established that the binary task on this
    data is trivially separable and its explanations are not citable evidence, so
    landing here IS the result: the K-way design could not be sustained.
    """
    return Decision(
        rung=RUNG_BINARY,
        rung_name=RUNG_NAMES[RUNG_BINARY],
        changed=True,
        terminal=True,
        vocabulary=(BENIGN_CLASS, "ATTACK"),
        exclusions=tuple(c for c in classes if c != BENIGN_CLASS),
        failing=failing,
        trigger_stats=stats,
        rationale=(
            f"{len(failing)}/{n_attack} attack classes fail the competence gate "
            f"({failing_fraction:.0%}, threshold {fraction:.0%})"
            + (f"; {extra}" if extra else "")
            + ". The ladder is exhausted: the design falls to the terminal binary rung "
              "and is reported as a NEGATIVE FINDING for the multi-class design."
        ),
    )
