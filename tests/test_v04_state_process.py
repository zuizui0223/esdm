import pytest

from esdm.domain import Context, StateSpace
from esdm.process import LinearState, NeutralState


def _state_process():
    return LinearState(
        state_space=StateSpace(("resting", "foraging", "moving")),
        reference_state="resting",
        covariates=("temp",),
        intercept_parameters={
            "foraging": "alpha_foraging",
            "moving": "alpha_moving",
        },
        coefficient_parameters={
            "foraging": {"temp": "beta_foraging_temp"},
            "moving": {"temp": "beta_moving_temp"},
        },
    )


def test_reference_state_has_no_free_parameter_and_zero_logit():
    process = _state_process()

    assert "resting" not in process.intercept_parameters
    assert set(process.priors()) == {
        "alpha_foraging",
        "alpha_moving",
        "beta_foraging_temp",
        "beta_moving_temp",
    }

    contribution = process.contribution(
        Context("s1", 1, 0),
        {
            "alpha_foraging": 0.2,
            "alpha_moving": -0.3,
            "beta_foraging_temp": 0.5,
            "beta_moving_temp": -0.2,
        },
        {"temp": 2.0},
    )
    assert contribution.channel == "state"
    assert contribution.labels == ("resting", "foraging", "moving")
    assert tuple(contribution.values) == pytest.approx((0.0, 1.2, -0.7))


def test_state_knockout_preserves_baseline_composition_and_removes_slopes():
    process = _state_process()
    knockout = process.knockout()

    assert isinstance(knockout, NeutralState)
    assert set(knockout.priors()) == {"alpha_foraging", "alpha_moving"}
    contribution = knockout.contribution(
        Context("s1", 1, 0),
        {"alpha_foraging": 0.2, "alpha_moving": -0.3},
        {"temp": 100.0},
    )
    assert tuple(contribution.values) == pytest.approx((0.0, 0.2, -0.3))


def test_state_process_rejects_reference_or_parameter_mismatch():
    states = StateSpace(("resting", "foraging"))
    with pytest.raises(ValueError):
        LinearState(
            state_space=states,
            reference_state="missing",
            covariates=(),
            intercept_parameters={"foraging": "alpha_foraging"},
            coefficient_parameters={"foraging": {}},
        )
    with pytest.raises(ValueError):
        LinearState(
            state_space=states,
            reference_state="resting",
            covariates=(),
            intercept_parameters={"resting": "alpha_resting"},
            coefficient_parameters={"foraging": {}},
        )


def test_state_process_rejects_duplicate_free_parameter_names():
    states = StateSpace(("resting", "foraging", "moving"))
    with pytest.raises(ValueError):
        LinearState(
            state_space=states,
            reference_state="resting",
            covariates=(),
            intercept_parameters={
                "foraging": "same_alpha",
                "moving": "same_alpha",
            },
            coefficient_parameters={"foraging": {}, "moving": {}},
        )
