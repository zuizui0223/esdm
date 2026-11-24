"""Post-hoc exhaustive, size-matched source-portfolio counterfactual tests."""
import math

from scripts.neobat_cc1_size_matched_control import (
    observed_portfolio_cv, size_matched_summary,
)


def sample(n=72):
    return {"rows": {
        f"2001-{(i // 30 + 1):02d}-{(i % 30 + 1):02d}": {
            "a a": float(1 + i % 5),
            "b b": float(1 + (i + 2) % 5),
            "c c": float(1 + (i + 4) % 5),
            "d d": float(1 + (i * 2) % 7),
        } for i in range(n)
    }}


def test_exact_k_combinations_with_no_resampling():
    src = sample()
    b = size_matched_summary(["a a", "b b", "c c", "d d"], [3, 4], src)
    assert len(b[3]) == math.comb(4, 3)
    assert len(b[4]) == math.comb(4, 4)
    assert all(math.isfinite(x) and x >= 0 for x in b[3] + b[4])


def test_same_portfolio_order_does_not_change_cv():
    src = sample()
    a, n = observed_portfolio_cv(["a a", "b b", "c c"], src)
    b, m = observed_portfolio_cv(["c c", "b b", "a a"], src)
    assert n == m == 72
    assert math.isclose(a, b, rel_tol=0, abs_tol=1e-13)


def test_missing_is_not_zero():
    src = sample()
    src["rows"]["2001-01-01"]["a a"] = None
    cv, n = observed_portfolio_cv(["a a", "b b", "c c"], src)
    assert n == 71 and cv is not None


def test_single_or_short_series_is_not_evaluable():
    assert observed_portfolio_cv([], sample()) == (None, 0)
    v, n = observed_portfolio_cv(["a a", "b b", "c c"], sample(8))
    assert v is None and n == 8
