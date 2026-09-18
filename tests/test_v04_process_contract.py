import math

from esdm.domain import Context
from esdm.process import LinearSuitability, ProcessContribution


def test_suitability_exposes_generic_contribution_without_changing_value():
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    ctx = Context("s1", 1, 0)
    theta = {"intercept": math.log(2.0), "beta_x": math.log(3.0)}
    covariates = {"x": 1.0}

    contribution = process.contribution(ctx, theta, covariates)

    assert isinstance(contribution, ProcessContribution)
    assert contribution.channel == "log_intensity"
    assert contribution.labels == ()
    assert contribution.values == process.log_intensity(ctx, theta, covariates)


def test_suitability_array_contribution_preserves_context_axis():
    import numpy as np

    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    keys = (("a", 1, 0), ("b", 1, 0))
    theta = {"intercept": 0.2, "beta_x": 0.5}
    covariates = {"x": np.asarray([-1.0, 2.0])}

    contribution = process.contribution_array(
        keys,
        theta,
        covariates,
        array_module=np,
    )

    assert contribution.channel == "log_intensity"
    assert contribution.labels == ()
    np.testing.assert_allclose(contribution.values, [-0.3, 1.2])
