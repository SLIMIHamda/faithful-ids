"""Multi-class target taxonomy (queue #5.1) — raw CICIDS labels -> canonical classes."""

from __future__ import annotations

import pandas as pd

from faithfulids.datasets.loaders.cicids2017 import (
    CANONICAL_CLASSES,
    canonical_class,
    class_index_map,
    feature_columns,
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
    assert m["BENIGN"] == 0 and set(m) == set(CANONICAL_CLASSES)
    assert len(m) == len(CANONICAL_CLASSES) == 8


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
