"""The pre-registered class-handling contingency (prereg amendment 0001).

One test per rung, plus the properties that make the rule auditable: the trigger
counts CLASSES not errors, resolution is one pass, the ladder descends one rung
per evaluation, and BENIGN is untouchable.
"""

from __future__ import annotations

import pytest

from faithfulids.detectors.contingency import (
    RUNG_BINARY,
    RUNG_EXCLUDED,
    RUNG_LEAF,
    RUNG_PARENT_MERGED,
    ContingencyExhausted,
    resolve,
)

TAXONOMY = {
    "canonical_classes": ["BENIGN", "DoS", "DDoS", "PortScan",
                          "FTP-Patator", "SSH-Patator", "Web Attack", "Bot"],
    "parents": {
        "BENIGN": "BENIGN", "DoS": "DoS", "DDoS": "DDoS", "PortScan": "PortScan",
        "FTP-Patator": "Brute Force", "SSH-Patator": "Brute Force",
        "Web Attack": "Web Attack", "Bot": "Bot",
    },
}

THRESHOLDS = {
    "recall_floor": 0.8,
    "min_support": 100,
    "class_failure_fraction": 0.5,
    "min_attack_classes": 3,
    "macro_f1_min": 0.9,
}


def table(recalls, *, n=500, macro_f1=0.95):
    """A competence table: {class -> recall}, or {class -> (recall, n)}."""
    per_family = {}
    for cls, val in recalls.items():
        recall, support = val if isinstance(val, tuple) else (val, n)
        per_family[cls] = {
            "n": support, "detection_recall": recall, "is_attack": cls != "BENIGN",
        }
    return {"macro_f1": macro_f1, "n": sum(r["n"] for r in per_family.values()),
            "per_family": per_family}


ALL_PASS = {"BENIGN": 0.99, "DoS": 0.95, "DDoS": 0.97, "PortScan": 0.96,
            "FTP-Patator": 0.92, "SSH-Patator": 0.88, "Web Attack": 0.85, "Bot": 0.83}


def _with(**overrides):
    return table({**ALL_PASS, **overrides})


# --------------------------------------------------------------------------- #
# Rung 1 — the vocabulary stands.
# --------------------------------------------------------------------------- #
def test_rung_one_when_every_class_is_certified():
    d = resolve(_with(), TAXONOMY, THRESHOLDS)
    assert d.rung == RUNG_LEAF and not d.changed and not d.terminal
    assert d.vocabulary == tuple(TAXONOMY["canonical_classes"])
    assert d.failing == () and d.merges == {} and d.exclusions == ()


def test_a_weak_detector_licenses_no_merge():
    """macro-F1 below its minimum with every class certified is a DETECTOR defect.
    The contingency must not launder it into a vocabulary change."""
    d = resolve(table(ALL_PASS, macro_f1=0.4), TAXONOMY, THRESHOLDS)
    assert d.detector_defect and not d.changed and d.rung == RUNG_LEAF
    assert "detector defect" in d.rationale


# --------------------------------------------------------------------------- #
# Rung 2 — the lineage fold.
# --------------------------------------------------------------------------- #
def test_rung_two_folds_the_whole_lineage_group_not_just_the_failing_member():
    """SSH-Patator fails alone, but the fold takes FTP-Patator with it: a parent
    holding one child is a rename, not a merge (and the taxonomy guard rejects
    that shape)."""
    d = resolve(_with(**{"SSH-Patator": 0.41}), TAXONOMY, THRESHOLDS)
    assert d.rung == RUNG_PARENT_MERGED and d.changed and not d.terminal
    assert d.merges == {"FTP-Patator": "Brute Force", "SSH-Patator": "Brute Force"}
    assert d.exclusions == () and d.failing == ("SSH-Patator",)
    assert d.vocabulary == ("BENIGN", "DoS", "DDoS", "PortScan", "Brute Force",
                            "Web Attack", "Bot")


def test_under_support_routes_through_the_contingency_like_a_floor_failure():
    """A class the evidence cannot speak about is not certified, so it is resolved
    — not silently passed because its point estimate happened to look fine."""
    d = resolve(_with(**{"FTP-Patator": (1.0, 12)}), TAXONOMY, THRESHOLDS)
    assert d.rung == RUNG_PARENT_MERGED
    assert d.trigger_stats["reasons"]["FTP-Patator"]["under_support"] is True
    assert d.trigger_stats["reasons"]["FTP-Patator"]["below_floor"] is False


# --------------------------------------------------------------------------- #
# Rung 3 — parentless failures.
# --------------------------------------------------------------------------- #
def test_rung_three_excludes_a_parentless_failing_class():
    """Bot bleeding into BENIGN is the a-priori candidate: it has no lineage
    parent, so rung 2 cannot help it. Without this rung one hard class would
    force the whole design to binary."""
    d = resolve(_with(Bot=0.31), TAXONOMY, THRESHOLDS)
    assert d.rung == RUNG_EXCLUDED and d.changed and not d.terminal
    assert d.exclusions == ("Bot",) and d.merges == {}
    assert "Bot" not in d.vocabulary and "BENIGN" in d.vocabulary
    assert "main text" in d.rationale


def test_one_pass_resolves_merges_and_exclusions_together():
    d = resolve(_with(Bot=0.30, **{"SSH-Patator": 0.42}), TAXONOMY, THRESHOLDS)
    assert d.rung == RUNG_EXCLUDED
    assert d.merges == {"FTP-Patator": "Brute Force", "SSH-Patator": "Brute Force"}
    assert d.exclusions == ("Bot",)
    assert d.trigger_stats["one_pass"] is True
    assert d.vocabulary == ("BENIGN", "DoS", "DDoS", "PortScan", "Brute Force",
                            "Web Attack")


def test_exclusion_rung_is_inadmissible_when_too_few_attack_classes_survive():
    """Below the registered minimum of surviving attack classes the exclusion rung
    stops being a K-way design at all, so the ladder goes terminal instead."""
    thin = {
        "canonical_classes": ["BENIGN", "PortScan", "Bot", "Web Attack"],
        "parents": {c: c for c in ["BENIGN", "PortScan", "Bot", "Web Attack"]},
    }
    d = resolve(table({"BENIGN": 0.99, "PortScan": 0.95, "Bot": 0.2, "Web Attack": 0.93}),
                thin, THRESHOLDS)
    assert d.rung == RUNG_BINARY and d.terminal
    assert "below the registered minimum" in d.rationale


# --------------------------------------------------------------------------- #
# The trigger: class-counted, global, one evaluation per rung.
# --------------------------------------------------------------------------- #
def test_at_or_above_the_fraction_the_design_descends_a_rung_instead():
    """>= half the attack classes failing is not a class-by-class problem. The
    resolver applies every available fold and re-gates there — it does NOT try to
    exclude four classes in one move."""
    d = resolve(_with(DoS=0.1, DDoS=0.2, PortScan=0.3, Bot=0.1), TAXONOMY, THRESHOLDS)
    assert d.trigger_stats["failing_fraction"] == pytest.approx(4 / 7)
    assert d.rung == RUNG_PARENT_MERGED and not d.terminal
    assert d.exclusions == ()  # no exclusions decided from rung-1 data
    assert "not salvageable class-by-class" in d.rationale


def test_the_trigger_counts_classes_not_errors():
    """A majority class failing badly must not mask (or manufacture) a verdict:
    what matters is how many CLASSES fail, whatever their support."""
    huge_class_fails = _with(**{"DoS": (0.1, 500_000)})
    d = resolve(huge_class_fails, TAXONOMY, THRESHOLDS)
    assert d.trigger_stats["n_failing"] == 1
    assert d.trigger_stats["failing_fraction"] == pytest.approx(1 / 7)
    assert d.rung == RUNG_EXCLUDED  # DoS is parentless -> excluded, not binary


def test_a_class_absent_from_the_evaluation_set_is_not_certified():
    """The hole this closes: iterating the TABLE's keys would let a canonical class
    that never appears in the competence split vanish from both the numerator and
    the denominator — silently untested rather than uncertified."""
    missing_bot = {k: v for k, v in ALL_PASS.items() if k != "Bot"}
    d = resolve(table(missing_bot), TAXONOMY, THRESHOLDS)
    assert "Bot" in d.failing
    assert d.trigger_stats["reasons"]["Bot"]["absent_from_evaluation_set"] is True
    assert d.trigger_stats["reasons"]["Bot"]["n"] == 0
    assert d.trigger_stats["n_attack_classes"] == 7  # denominator is the vocabulary


def test_the_trigger_is_scoped_to_the_fitted_vocabulary():
    """A run whose data covers only part of the taxonomy is certified against what
    it actually fitted; the uncovered canonical classes are RECORDED, not ignored."""
    fitted = ("BENIGN", "DoS", "DDoS", "PortScan")
    d = resolve(table({k: ALL_PASS[k] for k in fitted}), TAXONOMY, THRESHOLDS,
                vocabulary=fitted)
    assert d.rung == RUNG_LEAF and d.failing == ()
    assert d.trigger_stats["n_attack_classes"] == 3
    assert set(d.trigger_stats["absent_from_fit"]) == {
        "FTP-Patator", "SSH-Patator", "Web Attack", "Bot"}


def test_descent_is_one_rung_per_evaluation():
    """Called at rung 2 with the merged vocabulary still failing at scale, the
    only legal move is the terminal rung — never a jump computed from rung-1 data."""
    merged = {
        "canonical_classes": ["BENIGN", "DoS", "DDoS", "PortScan", "Brute Force",
                              "Web Attack", "Bot"],
        "parents": {c: c for c in ["BENIGN", "DoS", "DDoS", "PortScan",
                                   "Brute Force", "Web Attack", "Bot"]},
    }
    failing_wide = table({"BENIGN": 0.99, "DoS": 0.2, "DDoS": 0.2, "PortScan": 0.2,
                          "Brute Force": 0.2, "Web Attack": 0.9, "Bot": 0.9})
    d = resolve(failing_wide, merged, THRESHOLDS, current_rung=RUNG_PARENT_MERGED)
    assert d.rung == RUNG_BINARY and d.terminal
    assert d.vocabulary == ("BENIGN", "ATTACK")
    assert "NEGATIVE FINDING" in d.rationale


def test_the_ladder_refuses_to_fire_below_its_last_rung():
    with pytest.raises(ContingencyExhausted, match="terminal binary rung"):
        resolve(_with(Bot=0.1), TAXONOMY, THRESHOLDS, current_rung=RUNG_BINARY)


# --------------------------------------------------------------------------- #
# Invariants and record-keeping.
# --------------------------------------------------------------------------- #
def test_benign_is_never_merged_or_excluded_even_when_it_fails():
    """BENIGN is not an attack class: a poor benign recall is a detector problem
    (it also sinks macro-F1), never a reason to change the class vocabulary."""
    d = resolve(_with(BENIGN=0.10), TAXONOMY, THRESHOLDS)
    assert d.failing == () and not d.changed
    assert "BENIGN" not in d.merges and "BENIGN" not in d.exclusions


def test_resolve_is_pure_and_repeatable():
    t, args = _with(Bot=0.3), (TAXONOMY, THRESHOLDS)
    assert resolve(t, *args).as_record() == resolve(t, *args).as_record()
    assert TAXONOMY["canonical_classes"][0] == "BENIGN"  # inputs untouched
    assert TAXONOMY["parents"]["FTP-Patator"] == "Brute Force"


def test_decision_record_is_json_safe_and_names_its_evidence():
    import json

    d = resolve(_with(Bot=0.3), TAXONOMY, THRESHOLDS)
    rec = json.loads(json.dumps(d.as_record()))  # must round-trip for the manifest
    assert rec["rung_name"] == "parent_merged_minus_excluded"
    assert rec["trigger_stats"]["evaluated_at_rung"] == RUNG_LEAF
    assert rec["trigger_stats"]["recall_floor"] == 0.8
    assert rec["trigger_stats"]["reasons"]["Bot"]["detection_recall"] == 0.3


def test_the_real_committed_taxonomy_and_thresholds_drive_the_engine():
    """The engine reads the SHIPPED taxonomy and the FROZEN prereg values, not a
    fixture — if either drifts from what amendment 0001 registered, this fails."""
    from faithfulids.datasets.loaders.cicids2017 import load_taxonomy
    from faithfulids.orchestration.references import resolve_reference

    tax = load_taxonomy("cicids2017")
    th = {
        "recall_floor": resolve_reference(
            "statistics:decision_thresholds:detector_recall_floor")["value"],
        "min_support": resolve_reference(
            "statistics:decision_thresholds:detector_class_min_support")["value"],
        "class_failure_fraction": resolve_reference(
            "statistics:decision_thresholds:contingency_class_failure_fraction")["value"],
        "min_attack_classes": resolve_reference(
            "statistics:decision_thresholds:contingency_min_attack_classes")["value"],
        "macro_f1_min": resolve_reference(
            "statistics:decision_thresholds:detector_macro_f1_min")["value"],
    }
    d = resolve(_with(**{"SSH-Patator": 0.4}), tax, th)
    assert d.merges == {"FTP-Patator": "Brute Force", "SSH-Patator": "Brute Force"}
    # DoS/DDoS remain distinct at every rung — the withdrawn merge is unreachable
    assert resolve(_with(DoS=0.1), tax, th).merges == {}
    assert "Volumetric Flood" not in str(d.as_record())


# --------------------------------------------------------------------------- #
# Materialising a Decision as the next taxonomy (amendment 0001's "apply" step)
# --------------------------------------------------------------------------- #

FULL_TAXONOMY = {
    "id": "cicids2017", "schema_version": "v1", "kind": "class_taxonomy",
    "dataset": "cicids2017", "version": "1.1.0",
    **TAXONOMY,
    "label_map": {
        "benign": "BENIGN", "dos hulk": "DoS", "ddos": "DDoS", "portscan": "PortScan",
        "ftp patator": "FTP-Patator", "ssh patator": "SSH-Patator", "bot": "Bot",
        "web attack xss": "Web Attack", "infiltration": "excluded",
    },
}


def _apply(decision, taxonomy=None, version="2.0.0"):
    from faithfulids.detectors.contingency import apply_to_taxonomy

    return apply_to_taxonomy(taxonomy or FULL_TAXONOMY, decision, new_version=version)


def _taxonomy_is_valid(tax):
    """The same rules validate-configs enforces, so a written file cannot fail CI."""
    from faithfulids.orchestration.validate_configs import _parent_map_errors

    canon = set(tax["canonical_classes"])
    errors = _parent_map_errors(tax, canon, "t")
    errors += [f"label_map[{k!r}] -> {v!r}" for k, v in tax["label_map"].items()
               if v != "excluded" and v not in canon]
    errors += [f"orphan {c!r}" for c in tax["canonical_classes"]
               if c not in set(tax["label_map"].values())]
    return errors


def test_exclusion_rung_drops_the_class_and_keeps_its_raw_labels_visible():
    """The real 2026-07-24 case: Bot fails the floor, is parentless, is excluded.

    The raw label is retargeted to 'excluded', NOT deleted — a dropped key would
    make the loader silently ignore those rows instead of visibly excluding them.
    """
    decision = resolve(_with(Bot=0.77), TAXONOMY, THRESHOLDS)
    assert decision.rung == RUNG_EXCLUDED and decision.exclusions == ("Bot",)

    new = _apply(decision)
    assert "Bot" not in new["canonical_classes"]
    assert len(new["canonical_classes"]) == 7
    assert new["label_map"]["bot"] == "excluded"
    assert "bot" in new["label_map"]          # key kept, target changed
    assert new["label_map"]["infiltration"] == "excluded"  # already-excluded untouched
    assert "Bot" not in new["parents"]
    assert new["version"] == "2.0.0"
    # the lineage group Bot was not part of survives intact and stays available
    assert new["parents"]["FTP-Patator"] == new["parents"]["SSH-Patator"] == "Brute Force"
    assert _taxonomy_is_valid(new) == []


def test_merge_rung_collapses_the_group_to_a_parent_that_becomes_canonical():
    """A rung-2 merge folds BOTH siblings into the new parent name, which then is
    a canonical class in its own right (and so is its own parent)."""
    decision = resolve(_with(**{"SSH-Patator": 0.5}), TAXONOMY, THRESHOLDS)
    assert decision.rung == RUNG_PARENT_MERGED
    assert decision.merges == {"FTP-Patator": "Brute Force", "SSH-Patator": "Brute Force"}

    new = _apply(decision)
    assert "Brute Force" in new["canonical_classes"]
    assert "FTP-Patator" not in new["canonical_classes"]
    assert "SSH-Patator" not in new["canonical_classes"]
    # order is stable: the parent sits where the group's first member was
    assert new["canonical_classes"] == ["BENIGN", "DoS", "DDoS", "PortScan",
                                        "Brute Force", "Web Attack", "Bot"]
    assert new["label_map"]["ftp patator"] == new["label_map"]["ssh patator"] == "Brute Force"
    assert new["parents"]["Brute Force"] == "Brute Force"
    assert _taxonomy_is_valid(new) == []


def test_an_exclusion_that_leaves_one_sibling_dissolves_the_lineage_group():
    """A lone survivor cannot merge with itself, and validate-configs rejects a
    non-canonical parent with fewer than two children — so the group dissolves."""
    from faithfulids.detectors.contingency import Decision

    decision = Decision(
        rung=RUNG_EXCLUDED, rung_name="parent_merged_minus_excluded", changed=True,
        terminal=False,
        vocabulary=("BENIGN", "DoS", "DDoS", "PortScan", "SSH-Patator", "Web Attack", "Bot"),
        exclusions=("FTP-Patator",), failing=("FTP-Patator",),
    )
    new = _apply(decision)
    assert "Brute Force" not in new["parents"].values()
    assert new["parents"]["SSH-Patator"] == "SSH-Patator"
    assert _taxonomy_is_valid(new) == []


def test_apply_refuses_the_terminal_rung_and_a_decision_that_changes_nothing():
    """Rung 4 is a negative finding to report, not a vocabulary to fit; and a
    rung-1 'the vocabulary stands' decision has nothing to materialise."""
    from faithfulids.detectors.contingency import apply_to_taxonomy

    stands = resolve(table(ALL_PASS), TAXONOMY, THRESHOLDS)
    assert stands.changed is False
    with pytest.raises(ValueError, match="nothing to materialise"):
        apply_to_taxonomy(FULL_TAXONOMY, stands, new_version="2.0.0")

    binary = resolve(_with(DoS=0.1, DDoS=0.1, PortScan=0.1, Bot=0.1),
                     TAXONOMY, THRESHOLDS, current_rung=RUNG_PARENT_MERGED)
    assert binary.rung == RUNG_BINARY
    with pytest.raises(ValueError, match="NEGATIVE FINDING"):
        apply_to_taxonomy(FULL_TAXONOMY, binary, new_version="2.0.0")


def test_apply_refuses_a_decision_resolved_against_a_different_taxonomy():
    """Guards the ordering trap: applying a stale Decision to a taxonomy that has
    already moved would silently exclude a class that is no longer there."""
    from faithfulids.detectors.contingency import apply_to_taxonomy

    decision = resolve(_with(Bot=0.77), TAXONOMY, THRESHOLDS)
    already_applied = _apply(decision)  # Bot is gone
    with pytest.raises(ValueError, match="not canonical classes"):
        apply_to_taxonomy(already_applied, decision, new_version="3.0.0")


def test_decision_record_round_trips():
    """competence.json stores the Decision as a record; the apply step reads it
    back, so the two directions must agree exactly."""
    from faithfulids.detectors.contingency import Decision

    decision = resolve(_with(Bot=0.77), TAXONOMY, THRESHOLDS)
    assert Decision.from_record(decision.as_record()).as_record() == decision.as_record()
