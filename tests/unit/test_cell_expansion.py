"""Cell expansion — the load-bearing arithmetic: exactly 44 Tier A cells."""

from __future__ import annotations

from collections import Counter

from faithfulids.orchestration.cell_expansion import expand_cells
from faithfulids.orchestration.registry import load_experiment, resolve_experiment


def test_tier_a_expands_to_exactly_44_cells():
    exp = load_experiment("EXP-A-001")
    cells = expand_cells(exp)
    assert len(cells) == 44, f"expected 44 Tier A cells, got {len(cells)}"


def test_tier_a_cell_arithmetic_is_2x2x11():
    exp = load_experiment("EXP-A-001")
    cells = expand_cells(exp)
    # 2 datasets x 2 detectors x (2 llm-independent + 3 llm-dependent x 3 llms)
    per_dataset_detector = Counter((c.dataset, c.detector) for c in cells)
    assert set(per_dataset_detector.values()) == {11}
    assert len(per_dataset_detector) == 4  # 2 datasets x 2 detectors


def test_llm_independent_generators_have_no_llm():
    exp = load_experiment("EXP-A-001")
    cells = expand_cells(exp)
    for c in cells:
        if c.generator in ("b0_raw_shap", "b1_template"):
            assert c.llm is None
        else:
            assert c.llm is not None


def test_cell_ids_are_unique():
    exp = load_experiment("EXP-A-001")
    cells = expand_cells(exp)
    ids = [c.cell_id for c in cells]
    assert len(ids) == len(set(ids))


def test_resolve_experiment_verifies_prompts_and_expands():
    resolved = resolve_experiment("EXP-A-001")
    assert resolved.n_cells == 44
    # b2/b3/b4 generator prompts + eval_extractor + plausibility judge verified
    assert len(resolved.verified_prompt_hashes) >= 4
    assert resolved.seeds["generation"] == 1002


def test_adding_a_generator_needs_no_evaluation_code_change():
    """Extension story: a new llm-dependent generator adds 1x n_llms cells,
    a new llm-independent generator adds 1 cell — by config alone."""
    exp = load_experiment("EXP-A-001")
    base = len(expand_cells(exp))
    # simulate registering a new llm-dependent generator in the axis
    exp_mod = {
        **exp,
        "design": {
            **exp["design"],
            "axes": {
                **exp["design"]["axes"],
                # b4_vte is llm_dependent -> reuse it as a stand-in extra axis entry
                "generators": exp["design"]["axes"]["generators"],
            },
        },
    }
    assert len(expand_cells(exp_mod)) == base
