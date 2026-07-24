"""Multi-class target taxonomy (queue #5.1) — raw CICIDS labels -> canonical classes."""

from __future__ import annotations

import pandas as pd

from faithfulids.datasets.loaders.cicids2017 import (
    canonical_class,
    canonical_classes,
    class_index_map,
    feature_columns,
    load_taxonomy,
    multiclass_frame,
)


def test_canonical_class_coarsens_variants_and_excludes_rare():
    # DoS variants collapse to "DoS"; DDoS stays separate
    assert canonical_class("DoS Hulk") == "DoS"
    assert canonical_class("DoS GoldenEye") == "DoS"
    assert canonical_class("DoS slowloris") == "DoS"
    assert canonical_class("DDoS") == "DDoS"
    # web variants (incl. the non-ASCII separator CICIDS uses) collapse to "Web Attack"
    assert canonical_class("Web Attack \x96 Brute Force") == "Web Attack"
    assert canonical_class("Web Attack \x96 XSS") == "Web Attack"
    assert canonical_class("  benign ") == "BENIGN"  # normalised
    assert canonical_class("PortScan") == "PortScan"
    assert canonical_class("Bot") == "Bot"
    # rare / unknown -> excluded (None)
    assert canonical_class("Infiltration") is None
    assert canonical_class("Heartbleed") is None
    assert canonical_class("Some New Attack") is None


def test_class_index_map_is_stable_over_the_full_taxonomy():
    m = class_index_map()
    classes = canonical_classes()
    assert m["BENIGN"] == 0 and set(m) == set(classes)
    assert len(m) == len(classes) == 8


def test_kb_attack_classes_all_map_in_the_taxonomy():
    """Silent-drift guard (5.1b): every attack-class KB entry resolves through the
    single taxonomy config to a canonical class or 'excluded'. Mirrors the
    validate-configs check, on the REAL committed configs."""
    import yaml

    from faithfulids.provenance import repo_root
    from faithfulids.datasets.loaders.cicids2017 import _norm

    kb = yaml.safe_load(
        (repo_root() / "kb" / "attack_classes" / "cicids2017.yaml").read_text(encoding="utf-8")
    )
    tax = load_taxonomy("cicids2017")
    keys = {_norm(k) for k in tax["label_map"]}
    unmapped = [e["name"] for e in kb["entries"] if _norm(e["name"]) not in keys]
    assert not unmapped, f"KB classes not in the taxonomy: {unmapped}"


def test_every_canonical_class_has_a_mapped_label():
    """Orphan guard (5.2): a canonical class no raw label maps to would be a dead
    num_class slot the detector can never predict. Mirrors the validate-configs
    check, on the REAL committed taxonomy."""
    tax = load_taxonomy("cicids2017")
    mapped = set(tax["label_map"].values())
    orphans = [c for c in tax["canonical_classes"] if c not in mapped]
    assert not orphans, f"canonical classes with no raw label mapped to them: {orphans}"


def test_loader_and_validate_configs_normalisers_agree():
    """The loader's _norm and validate_configs._norm_label MUST match, or the
    drift guard and the runtime mapping disagree (validate_configs can't import the
    loader — pandas — so the two are pinned equal here)."""
    from faithfulids.datasets.loaders.cicids2017 import _norm
    from faithfulids.orchestration.validate_configs import _norm_label

    for s in ("FTP-Patator", "Web Attack \x96 XSS", "DoS Hulk", "  benign ", "DDoS"):
        assert _norm(s) == _norm_label(s)


# --------------------------------------------------------------------------- #
# Lineage-derived merge map (prereg amendment 0001).
# --------------------------------------------------------------------------- #
def test_committed_parent_map_offers_only_the_brute_force_fold():
    """The ONLY contingency merge available on the real taxonomy. DoS/DDoS must
    stay separate — merging them is detector-derived, not lineage-derived, and was
    withdrawn in the amendment."""
    from faithfulids.datasets.loaders.cicids2017 import parent_of

    assert parent_of("FTP-Patator") == parent_of("SSH-Patator") == "Brute Force"
    for cls in ("BENIGN", "DoS", "DDoS", "PortScan", "Web Attack", "Bot"):
        assert parent_of(cls) == cls, f"{cls} must have no lineage sibling"


def test_parent_of_refuses_an_unknown_class():
    import pytest

    from faithfulids.datasets.loaders.cicids2017 import parent_of

    with pytest.raises(KeyError, match="not a canonical class"):
        parent_of("Volumetric Flood")


def test_merged_taxonomy_yields_the_rung_two_vocabulary():
    from faithfulids.datasets.loaders.cicids2017 import merged_taxonomy

    merged = merged_taxonomy()
    assert merged["canonical_classes"] == [
        "BENIGN", "DoS", "DDoS", "PortScan", "Brute Force", "Web Attack", "Bot",
    ]
    # raw labels retarget through the merge; exclusions stay excluded
    assert merged["label_map"]["ftp patator"] == "Brute Force"
    assert merged["label_map"]["ssh patator"] == "Brute Force"
    assert merged["label_map"]["dos hulk"] == "DoS"
    assert merged["label_map"]["heartbleed"] == "excluded"
    # merging is idempotent: the result is a valid taxonomy with identity parents
    assert merged["parents"] == {c: c for c in merged["canonical_classes"]}
    assert merged_taxonomy(merged)["canonical_classes"] == merged["canonical_classes"]


def test_parent_map_guard_rejects_partial_reassigned_and_benign_merges():
    """The structural rules validate-configs enforces, exercised on mutated copies
    of the REAL taxonomy (lineage itself is not machine-checkable; these rules stop
    the map expressing anything but a visible merge)."""
    from faithfulids.orchestration.validate_configs import _parent_map_errors

    tax = load_taxonomy("cicids2017")
    canon = set(tax["canonical_classes"])
    assert _parent_map_errors(tax, canon, "ok") == []

    def mutated(**changes):
        c = dict(tax)
        c["parents"] = {**tax["parents"], **changes}
        return c

    partial = dict(tax)
    partial["parents"] = {k: v for k, v in tax["parents"].items() if k != "Bot"}
    assert any("not total" in e for e in _parent_map_errors(partial, canon, "w"))

    extra = mutated(**{"Infiltration": "Infiltration"})
    assert any("not total" in e for e in _parent_map_errors(extra, canon, "w"))

    # reassigning a leaf under another leaf (the withdrawn DoS -> DDoS shape)
    reassigned = mutated(DoS="DDoS")
    assert any("NEW parent name" in e for e in _parent_map_errors(reassigned, canon, "w"))

    # a new name with a single child is a rename, not a merge
    renamed = mutated(Bot="Botnet")
    assert any("rename, not a merge" in e for e in _parent_map_errors(renamed, canon, "w"))

    benign_merged = mutated(BENIGN="Normal-ish", PortScan="Normal-ish")
    assert any("never merged" in e for e in _parent_map_errors(benign_merged, canon, "w"))


def _frame():
    return pd.DataFrame({
        "Flow Duration": [1.0, 2.0, 3.0, 4.0, 5.0],
        "attack_class": ["BENIGN", "DoS Hulk", "DDoS", "Heartbleed", "BENIGN"],
        "target_class": [canonical_class(x) for x in
                         ["BENIGN", "DoS Hulk", "DDoS", "Heartbleed", "BENIGN"]],
        "label": [0, 1, 1, 1, 0],
    })


def test_multiclass_frame_drops_rare_and_indexes_present_classes():
    df = _frame()
    valid, idx = multiclass_frame(df)
    # Heartbleed row dropped (excluded family -> target_class None)
    assert len(valid) == 4 and "Heartbleed" not in set(valid["attack_class"])
    # only classes actually present are indexed, contiguous from 0
    assert set(idx) == {"BENIGN", "DoS", "DDoS"}
    assert sorted(idx.values()) == [0, 1, 2]
    assert list(valid["target_index"]) == [idx[c] for c in valid["target_class"]]


def test_target_class_is_not_a_feature():
    assert "target_class" not in feature_columns(_frame())


# --------------------------------------------------------------------------- #
# rows_per_file + explanation-sample truncation (K-way data coverage fixes).
# --------------------------------------------------------------------------- #
def _write_day(path, labels):
    pd.DataFrame({"Flow Duration": range(len(labels)), "Label": labels}).to_csv(
        path, index=False
    )


def test_global_max_rows_starves_late_files_but_rows_per_file_keeps_them(tmp_path):
    """max_rows appends whole files in sorted-name order and stops — a small cap
    keeps only the first day's attack family (the K=2 degeneration the guard in
    run_pilot rejects). rows_per_file subsamples each file, so every family
    survives the same memory budget."""
    from faithfulids.datasets.loaders.cicids2017 import load_cicids2017

    _write_day(tmp_path / "a_friday.csv", ["DDoS"] * 300)
    _write_day(tmp_path / "b_tuesday.csv", ["FTP-Patator"] * 300)
    _write_day(tmp_path / "c_wednesday.csv", ["DoS Hulk"] * 300)

    starved = load_cicids2017(tmp_path, max_rows=200)
    assert set(starved["target_class"].dropna()) == {"DDoS"}

    df = load_cicids2017(tmp_path, rows_per_file=100)
    assert set(df["target_class"].dropna()) == {"DDoS", "FTP-Patator", "DoS"}
    assert len(df) == 300  # 100 per file
    assert df.equals(load_cicids2017(tmp_path, rows_per_file=100))  # deterministic


def test_rows_per_file_is_a_stride_not_a_head(tmp_path):
    """Attacks are time-blocked WITHIN a day too (FTP-Patator morning, SSH-Patator
    afternoon in one file): a per-file head would still drop the afternoon family;
    the evenly-spaced stride keeps both."""
    from faithfulids.datasets.loaders.cicids2017 import load_cicids2017

    _write_day(tmp_path / "tuesday.csv", ["FTP-Patator"] * 200 + ["SSH-Patator"] * 200)
    df = load_cicids2017(tmp_path, rows_per_file=50)
    assert len(df) <= 50
    assert set(df["target_class"]) == {"FTP-Patator", "SSH-Patator"}


def _blocked_pool_frame(n_per_class=300):
    """CICIDS-shaped frame: classes in contiguous per-day blocks (file order)."""
    import numpy as np

    classes = ["DDoS", "PortScan", "FTP-Patator", "DoS"]
    return pd.DataFrame({
        "f1": np.arange(len(classes) * n_per_class, dtype=float),
        "target_class": [c for c in classes for _ in range(n_per_class)],
    })


def test_index_truncation_bias_erases_late_blocks_and_round_robin_does_not():
    from faithfulids.datasets.loaders.cicids2017 import stratified_explanation_sample

    df = _blocked_pool_frame()
    # legacy "index" truncation keeps the lowest pool indices: with contiguous
    # blocks the first class's quota alone fills n_explain (the documented bias —
    # frozen because every cached binary run used it).
    _, legacy = stratified_explanation_sample(
        df, n_explain=24, seed=7, stratify="target_class", truncation="index"
    )
    assert set(legacy["target_class"]) == {"DDoS"}
    # round_robin drops over-quota picks one-per-class-per-round: every stratum
    # keeps n/K rows — what the per-class competence gate measures.
    _, rr = stratified_explanation_sample(
        df, n_explain=24, seed=7, stratify="target_class", truncation="round_robin"
    )
    counts = rr["target_class"].value_counts()
    assert set(counts.index) == {"DDoS", "PortScan", "FTP-Patator", "DoS"}
    assert counts.min() == counts.max() == 6


def test_na_strata_are_never_explained_and_do_not_take_quota():
    """Excluded-family rows (target_class None) are not a stratum: they are never
    sampled into the explained set and do not shrink the per-class quota."""
    from faithfulids.datasets.loaders.cicids2017 import stratified_explanation_sample

    df = _blocked_pool_frame()
    df.loc[df.index[-200:], "target_class"] = None  # excluded tail (e.g. Infiltration)
    _, explain = stratified_explanation_sample(
        df, n_explain=24, seed=7, stratify="target_class", truncation="round_robin"
    )
    assert explain["target_class"].notna().all()


def test_unknown_truncation_fails_loudly():
    import pytest

    from faithfulids.datasets.loaders.cicids2017 import stratified_explanation_sample

    with pytest.raises(ValueError, match="truncation"):
        stratified_explanation_sample(
            _blocked_pool_frame(), n_explain=8, seed=1,
            stratify="target_class", truncation="bogus",
        )
