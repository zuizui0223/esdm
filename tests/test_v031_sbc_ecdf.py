from esdm.identify import (
    ess_thin_draws,
    sbc_ecdf_simultaneous_test,
)


def _balanced_ranks(draw_count=9, repeats=10):
    ranks = tuple(rank for _ in range(repeats) for rank in range(draw_count + 1))
    counts = tuple(draw_count for _ in ranks)
    return ranks, counts


def test_ess_thinning_records_effective_draw_support():
    thinned = ess_thin_draws(tuple(range(20)), effective_sample_size=5.0)
    assert thinned.stride == 4
    assert thinned.draws == (0, 4, 8, 12, 16)
    assert thinned.draw_count == 5


def test_ecdf_simultaneous_test_accepts_balanced_discrete_uniform_ranks():
    ranks_a, counts_a = _balanced_ranks()
    ranks_b, counts_b = _balanced_ranks()
    result = sbc_ecdf_simultaneous_test(
        ranks={"a": ranks_a, "b": ranks_b},
        draw_counts={"a": counts_a, "b": counts_b},
        alpha=0.05,
        simulations=2000,
        seed=20260918,
        evaluation_points=19,
    )
    assert result.passed
    assert set(result.parameter_max_deviation) == {"a", "b"}
    assert result.observed_max_deviation <= result.critical_max_deviation


def test_ecdf_simultaneous_test_rejects_one_bad_parameter_familywise():
    ranks_good, counts_good = _balanced_ranks()
    ranks_bad = tuple(0 for _ in ranks_good)
    counts_bad = counts_good
    result = sbc_ecdf_simultaneous_test(
        ranks={"good": ranks_good, "bad": ranks_bad},
        draw_counts={"good": counts_good, "bad": counts_bad},
        alpha=0.05,
        simulations=2000,
        seed=20260918,
        evaluation_points=19,
    )
    assert not result.passed
    assert result.parameter_max_deviation["bad"] > result.critical_max_deviation


def test_ecdf_simultaneous_test_supports_variable_rank_supports():
    draw_counts = tuple(4 + (i % 4) for i in range(80))
    ranks = tuple(i % (draw_count + 1) for i, draw_count in enumerate(draw_counts))
    result = sbc_ecdf_simultaneous_test(
        ranks={"theta": ranks},
        draw_counts={"theta": draw_counts},
        alpha=0.05,
        simulations=500,
        seed=17,
        evaluation_points=15,
    )
    assert result.critical_max_deviation > 0.0
    assert result.parameter_max_deviation["theta"] >= 0.0
