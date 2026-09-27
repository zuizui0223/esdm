import math

import pytest

from esdm.domain import Context
from esdm.process import LinearActivity, NeutralActivity


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def test_linear_activity_emits_additive_logit_contribution():
    process = LinearActivity(
        covariates=("temp",),
        intercept_parameter="activity_intercept",
        coefficient_parameters={"temp": "activity_beta_temp"},
    )
    contribution = process.contribution(
        Context("s1", 1, 0),
        {"activity_intercept": -0.4, "activity_beta_temp": 0.8},
        {"temp": 1.5},
    )

    assert contribution.channel == "activity"
    assert contribution.labels == ()
    assert contribution.values == pytest.approx(0.8)
    assert _sigmoid(contribution.values) == pytest.approx(_sigmoid(0.8))


def test_activity_knockout_preserves_intercept_and_removes_slopes():
    process = LinearActivity(
        covariates=("temp",),
        intercept_parameter="activity_intercept",
        coefficient_parameters={"temp": "activity_beta_temp"},
    )
    knockout = process.knockout()

    assert isinstance(knockout, NeutralActivity)
    assert knockout.knockout_semantics == (
        "preserve_baseline_neutralize_environmental_slopes"
    )
    assert set(knockout.priors()) == {"activity_intercept"}
    assert knockout.requires == frozenset()
    assert knockout.contribution(
        Context("s1", 1, 0),
        {"activity_intercept": -0.4},
        {"temp": 99.0},
    ).values == pytest.approx(-0.4)


def test_linear_activity_validates_covariate_parameter_contract():
    with pytest.raises(ValueError):
        LinearActivity(
            covariates=("temp",),
            intercept_parameter="activity_intercept",
            coefficient_parameters={},
        )

    with pytest.raises(ValueError):
        LinearActivity(
            covariates=("temp", "temp"),
            intercept_parameter="activity_intercept",
            coefficient_parameters={"temp": "activity_beta_temp"},
        )
