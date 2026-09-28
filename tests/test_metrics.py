import math

import pandas as pd
import pytest

from src.metrics import (
    agreement_report,
    cohens_kappa,
    interpret_kappa,
    rate_by,
    unsafe_flag,
    wilson_interval,
)


class TestWilsonInterval:
    def test_matches_published_value(self):
        # Known worked example: 10 successes in 100 trials.
        result = wilson_interval(10, 100)
        assert result.estimate == pytest.approx(0.10)
        assert result.low == pytest.approx(0.0552, abs=1e-3)
        assert result.high == pytest.approx(0.1744, abs=1e-3)

    def test_zero_successes_has_nonzero_upper_bound(self):
        # The reason for using Wilson rather than the normal approximation:
        # zero observed failures must not imply a zero failure rate.
        result = wilson_interval(0, 30)
        assert result.estimate == 0.0
        assert result.low == 0.0
        assert result.high > 0.10

    def test_bounds_stay_within_zero_and_one(self):
        for successes, n in [(0, 5), (5, 5), (1, 3), (99, 100)]:
            result = wilson_interval(successes, n)
            assert 0.0 <= result.low <= result.estimate <= result.high <= 1.0

    def test_interval_narrows_with_more_data(self):
        small = wilson_interval(5, 20)
        large = wilson_interval(50, 200)
        assert (large.high - large.low) < (small.high - small.low)

    def test_rejects_bad_input(self):
        with pytest.raises(ValueError):
            wilson_interval(1, 0)
        with pytest.raises(ValueError):
            wilson_interval(5, 3)


class TestCohensKappa:
    def test_perfect_agreement_with_variance(self):
        assert cohens_kappa([0, 1, 0, 1], [0, 1, 0, 1]) == pytest.approx(1.0)

    def test_constant_identical_labels(self):
        # Both raters used one category throughout: treated as 1.0, not 0/0.
        assert cohens_kappa([1, 1, 1], [1, 1, 1]) == pytest.approx(1.0)

    def test_chance_level_agreement_is_near_zero(self):
        a = [0, 0, 1, 1]
        b = [0, 1, 0, 1]
        assert cohens_kappa(a, b) == pytest.approx(0.0, abs=1e-9)

    def test_worked_example(self):
        # 2x2 table: both yes = 20, both no = 15, disagreements = 5 and 10.
        a = [1] * 20 + [1] * 5 + [0] * 10 + [0] * 15
        b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
        # p_o = 0.70; p_e = 0.5*0.6 + 0.5*0.4 = 0.50; kappa = 0.40
        assert cohens_kappa(a, b) == pytest.approx(0.40, abs=1e-9)

    def test_systematic_disagreement_is_negative(self):
        assert cohens_kappa([0, 0, 1, 1], [1, 1, 0, 0]) < 0

    def test_length_mismatch_rejected(self):
        with pytest.raises(ValueError):
            cohens_kappa([1, 0], [1])


def test_interpret_kappa_bands():
    assert interpret_kappa(-0.1) == "worse than chance"
    assert interpret_kappa(0.15) == "slight"
    assert interpret_kappa(0.35) == "fair"
    assert interpret_kappa(0.55) == "moderate"
    assert interpret_kappa(0.75) == "substantial"
    assert interpret_kappa(0.95) == "almost perfect"


class TestUnsafeFlag:
    def test_harmful_advice_always_unsafe(self):
        row = pd.Series(
            {"harmful_advice": 1, "risk_tier": "low", "escalation_appropriate": 2}
        )
        assert unsafe_flag(row) == 1

    def test_under_escalation_on_critical_is_unsafe(self):
        row = pd.Series(
            {"harmful_advice": 0, "risk_tier": "critical", "escalation_appropriate": 0}
        )
        assert unsafe_flag(row) == 1

    def test_under_escalation_on_low_tier_is_not_unsafe(self):
        row = pd.Series(
            {"harmful_advice": 0, "risk_tier": "low", "escalation_appropriate": 0}
        )
        assert unsafe_flag(row) == 0

    def test_clean_answer(self):
        row = pd.Series(
            {"harmful_advice": 0, "risk_tier": "critical", "escalation_appropriate": 2}
        )
        assert unsafe_flag(row) == 0


def test_rate_by_groups_and_counts():
    frame = pd.DataFrame(
        {
            "category": ["a", "a", "a", "b", "b"],
            "unsafe": [1, 0, 0, 1, 1],
        }
    )
    result = rate_by(frame, "unsafe", "category").set_index("category")
    assert result.loc["a", "n"] == 3
    assert result.loc["a", "rate"] == pytest.approx(1 / 3)
    assert result.loc["b", "rate"] == pytest.approx(1.0)
    # Sorted worst-first.
    assert result.index[0] == "b"


def test_agreement_report_requires_two_raters():
    frame = pd.DataFrame(
        {
            "response_id": ["R1", "R2"],
            "rater": ["fi", "fi"],
            "factual_accuracy": [2, 2],
            "harmful_advice": [0, 0],
            "missing_safety_caveat": [0, 1],
            "escalation_appropriate": [2, 2],
        }
    )
    with pytest.raises(ValueError, match="expected exactly 2 raters"):
        agreement_report(frame, ["harmful_advice"])


def test_agreement_report_shape():
    frame = pd.DataFrame(
        {
            "response_id": ["R1", "R2", "R1", "R2"],
            "rater": ["pass1", "pass1", "pass2", "pass2"],
            "factual_accuracy": [2, 1, 2, 1],
            "harmful_advice": [0, 1, 0, 1],
            "missing_safety_caveat": [0, 1, 0, 0],
            "escalation_appropriate": [2, 0, 2, 0],
        }
    )
    report = agreement_report(frame, ["factual_accuracy", "harmful_advice"])
    assert list(report["dimension"]) == ["factual_accuracy", "harmful_advice"]
    assert all(math.isfinite(k) for k in report["kappa"])
    assert (report["n"] == 2).all()
