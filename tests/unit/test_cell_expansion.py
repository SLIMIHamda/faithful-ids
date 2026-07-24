"""Cell expansion — the load-bearing arithmetic of the Tier-A fractional design.

2026-07-18 revision (see CHANGELOG): the single 44-cell factorial became an
anchor factorial (EXP-A-001: 1 dataset x 1 K-way detector x 4-LLM scale ladder
x B0-B5 = 2 + 4x4 = 18 cells at N=400) plus three generality spokes at the
anchor LLM (EXP-A-002..004: 2 + 4x1 = 6 cells each at N=150) — 36 registered
Tier-A cells total.
"""

from __future__ import annotations

from collections import Counter

from faithfulids.orchestration.cell_expansion import expand_cells
from faithfulids.orchestration.registry import load_experiment, resolve_experiment

SPOKES = ("EXP-A-002", "EXP-A-003", "EXP-A-004")


def test_anchor_expands_to_exactly_18_cells():
    exp = load_experiment("EXP-A-001")
    cells = expand_cells(exp)
    # 1 dataset x 1 detector x (2 llm-independent + 4 llm-dependent x 4 llms)
    assert len(cells) == 18, f"expected 18 anchor cells, got {len(cells)}"
    per_dataset_detector = Counter((c.dataset, c.detector) for c in cells)
    assert per_dataset_detector == {("cicids2017_corrected", "xgboost_multiclass"): 18}


def test_each_spoke_expands_to_6_cells_and_the_square_closes():
    combos = set()
    for spoke in SPOKES:
        cells = expand_cells(load_experiment(spoke))
        assert len(cells) == 6, f"{spoke}: expected 6 cells, got {len(cells)}"
        assert {c.llm for c in cells} == {"qwen3_8b_4bit", None}  # anchor LLM only
        combos |= {(c.dataset, c.detector) for c in cells}
    # spokes + anchor close the 2x2 (dataset x detector) generality square
    combos.add(("cicids2017_corrected", "xgboost_multiclass"))
    assert combos == {
        ("cicids2017_corrected", "xgboost_multiclass"),
        ("cicids2017_corrected", "random_forest_multiclass"),
        ("unsw_nb15", "xgboost_multiclass"),
        ("unsw_nb15", "random_forest_multiclass"),
    }


def test_tier_a_total_is_36_cells():
    total = sum(len(expand_cells(load_experiment(e))) for e in ("EXP-A-001", *SPOKES))
    assert total == 36


def test_llm_independent_generators_have_no_llm():
    for e in ("EXP-A-001", *SPOKES):
        for c in expand_cells(load_experiment(e)):
            if c.generator in ("b0_raw_shap", "b1_template"):
                assert c.llm is None
            else:
                assert c.llm is not None


def test_cell_ids_are_unique_across_tier_a():
    ids = [c.cell_id for e in ("EXP-A-001", *SPOKES)
           for c in expand_cells(load_experiment(e))]
    assert len(ids) == len(set(ids))


def test_resolve_experiment_verifies_prompts_and_expands():
    resolved = resolve_experiment("EXP-A-001")
    assert resolved.n_cells == 18
    # b2/b3/b4/b5 generator prompts (+multiclass variants) + extractor + judge
    assert len(resolved.verified_prompt_hashes) >= 5
    assert resolved.seeds["generation"] == 1002


def test_registry_index_lists_every_registered_experiment():
    """REGISTRY.md is described as the append-only index the paper's appendix is
    generated from, "so nothing can be silently omitted" — but nothing checked it
    against the registered files, and three Tier-A spokes had in fact gone
    unlisted. This is that check."""
    import re

    from faithfulids.orchestration.registry import experiments_root, load_all_experiments

    table = (experiments_root() / "REGISTRY.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"^\|\s*(EXP-[A-Z0-9-]+|ANCHOR)\s*\|", table, re.MULTILINE))
    registered = set(load_all_experiments())

    assert not (registered - listed), f"registered but not in REGISTRY.md: {registered - listed}"
    assert not (listed - registered), f"in REGISTRY.md but not registered: {listed - registered}"


def test_the_contingency_smoke_gate_cannot_spend_tokens():
    """EXP-G-003 settles the class vocabulary BEFORE generation (amendment 0001
    sequencing). A registered LLM on it would defeat the purpose, so the null is
    pinned here rather than left to the driver."""
    exp = load_experiment("EXP-G-003")
    assert exp["design"]["mode"] == "single"
    assert exp["design"]["cell"]["llm"] is None
    assert exp["design"]["cell"]["detector"] == "xgboost_multiclass"
    assert exp["gate"]["criterion"] == "detector_competence"
    assert exp["metric_refs"] == []  # no explanation metrics: nothing is explained
