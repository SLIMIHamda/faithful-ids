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
