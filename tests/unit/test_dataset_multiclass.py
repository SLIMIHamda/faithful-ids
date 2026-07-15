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


def test_loader_and_validate_configs_normalisers_agree():
    """The loader's _norm and validate_configs._norm_label MUST match, or the
    drift guard and the runtime mapping disagree (validate_configs can't import the
    loader — pandas — so the two are pinned equal here)."""
    from faithfulids.datasets.loaders.cicids2017 import _norm
    from faithfulids.orchestration.validate_configs import _norm_label

    for s in ("FTP-Patator", "Web Attack \x96 XSS", "DoS Hulk", "  benign ", "DDoS"):
        assert _norm(s) == _norm_label(s)


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
