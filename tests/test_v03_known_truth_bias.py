import math


def test_effort_gradient_bias_matches_log_effort_projection():
    from esdm.simulate.misspecified import effort_gradient_apparent_slope

    x = (-1.5, -0.5, 0.5, 1.5)
    true_beta = 0.6
    gamma = 0.7
    effort = tuple(math.exp(gamma * value) for value in x)

    apparent = effort_gradient_apparent_slope(
        true_beta=true_beta,
        covariate=x,
        true_effort=effort,
        assumed_effort=1.0,
    )
    assert math.isclose(apparent, true_beta + gamma, rel_tol=1e-12, abs_tol=1e-12)


def test_omitted_driver_bias_matches_linear_projection():
    from esdm.simulate.misspecified import omitted_driver_apparent_slope

    x = (-1.5, -0.5, 0.5, 1.5)
    hidden = tuple(0.8 * value for value in x)
    apparent = omitted_driver_apparent_slope(
        true_beta=0.4,
        omitted_beta=0.75,
        covariate=x,
        hidden_driver=hidden,
    )
    assert math.isclose(apparent, 0.4 + 0.75 * 0.8, rel_tol=1e-12, abs_tol=1e-12)


def test_bias_helpers_reject_zero_variance_covariate():
    import pytest
    from esdm.simulate.misspecified import (
        effort_gradient_apparent_slope,
        omitted_driver_apparent_slope,
    )

    with pytest.raises(ValueError):
        effort_gradient_apparent_slope(
            true_beta=0.5,
            covariate=(1.0, 1.0, 1.0),
            true_effort=(1.0, 2.0, 3.0),
            assumed_effort=1.0,
        )
    with pytest.raises(ValueError):
        omitted_driver_apparent_slope(
            true_beta=0.5,
            omitted_beta=0.5,
            covariate=(1.0, 1.0, 1.0),
            hidden_driver=(0.0, 1.0, 2.0),
        )
