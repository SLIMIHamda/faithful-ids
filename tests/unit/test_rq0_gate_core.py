"""EXP-G-002 pure cores: ROC operating point + matched-pairs battery verdict."""

from __future__ import annotations

from faithfulids.metrics.meta import find_operating_point
from faithfulids.orchestration.rq0_gate import battery_summary


def test_operating_point_separates_clean_distributions():
    # faithful scores 1.0, corrupted 0.8 -> a threshold between them, J = 1
    r = find_operating_point([1.0, 1.0, 1.0, 0.8, 0.8], [0, 0, 0, 1, 1])
    assert r["sensitivity"] == 1.0 and r["specificity"] == 1.0
    assert 0.8 < r["threshold"] < 1.0 and r["youden_j"] == 1.0


def test_operating_point_higher_is_corrupt_polarity():
    # hfr-style: corrupted HIGHER
    r = find_operating_point([0.0, 0.0, 0.2, 0.2], [0, 0, 1, 1], lower_is_corrupt=False)
    assert r["sensitivity"] == 1.0 and r["specificity"] == 1.0


def test_operating_point_degenerate_constant_metric():
    r = find_operating_point([1.0, 1.0, 1.0], [0, 1, 1])
    assert r["sensitivity"] in (0.0, 1.0)  # no separation possible, no crash


def test_battery_matched_pairs_verdict():
    scores = {
        # dsa_asserted: perfect on its designated operator, blind to rank_inversion
        "dsa_asserted": {"faithful": [1.0] * 4, "sign_flip": [0.8] * 4,
                         "rank_inversion": [1.0] * 4},
        # arc: perfect on rank_inversion
        "arc": {"faithful": [1.0] * 4, "sign_flip": [1.0] * 4,
                "rank_inversion": [0.9] * 4},
    }
    designations = {"sign_flip": ["dsa_asserted"], "rank_inversion": ["arc"],
                    "magnitude_inflation": []}
    summaries, verdict = battery_summary(scores, designations, sens_min=0.9, spec_min=0.9)
    assert verdict["passed"] is True
    assert verdict["blind_spot_operators"] == ["magnitude_inflation"]
    assert set(verdict["admissible_metrics"]) == {"arc", "dsa_asserted"}
    # blindness is reported but NOT a failure (matched pairs, not all-operators)
    assert summaries["dsa_asserted"]["per_operator_sensitivity"]["rank_inversion"] == 0.0


def test_battery_fails_when_a_designated_pair_misses():
    scores = {"dsa_asserted": {"faithful": [1.0] * 4, "sign_flip": [1.0] * 4}}  # blind!
    summaries, verdict = battery_summary(
        scores, {"sign_flip": ["dsa_asserted"]}, sens_min=0.9, spec_min=0.9
    )
    assert verdict["passed"] is False
    assert any("sign_flip" in f for f in verdict["failures"])
    assert summaries["dsa_asserted"]["admissible"] is False
