"""
Unit test for the priority-score weighting logic, mirrored in Python so the
formula can be tested without a live database (the SQL version in
sql/analytics/priority_score.sql is the source of truth for production).
"""

WEIGHTS = {
    "severity": 0.30, "frequency": 0.20, "growth": 0.15,
    "repeat": 0.15, "population": 0.10, "delay": 0.10,
}


def compute_priority_score(normalized_factors: dict) -> float:
    return round(sum(WEIGHTS[k] * normalized_factors.get(k, 0) for k in WEIGHTS), 3)


def test_priority_score_all_max_factors_equals_one():
    factors = {k: 1.0 for k in WEIGHTS}
    assert compute_priority_score(factors) == 1.0


def test_priority_score_all_zero_factors_equals_zero():
    factors = {k: 0.0 for k in WEIGHTS}
    assert compute_priority_score(factors) == 0.0


def test_priority_score_missing_factor_treated_as_zero():
    factors = {"severity": 1.0}  # everything else missing
    assert compute_priority_score(factors) == WEIGHTS["severity"]


def test_priority_score_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 5) == 1.0
