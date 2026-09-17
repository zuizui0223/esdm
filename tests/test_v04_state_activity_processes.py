import math

from esdm.domain import Context, StateSpace
from esdm.process import CategoricalActivityProcess, CategoricalStateProcess


def test_categorical_state_process_is_normalized_and_covariate_conditioned():
    process = CategoricalStateProcess(
        state_space=StateSpace(("juvenile", "adult", "dormant")),
        reference_state="juvenile",
        covariates=("season",),
        intercept_parameters={"adult": "state_adult", "dormant": "state_dormant"},
        coefficient_parameters={
            "adult": {"season": "state_adult_season"},
            "dormant": {"season": "state_dormant_season"},
        },
    )
    theta = {
        "state_adult": 0.2,
        "state_dormant": -0.4,
        "state_adult_season": 1.0,
        "state_dormant_season": -0.8,
    }
    early = process.probabilities(Context("site", 30, 12), theta, {"season": -1.0})
    late = process.probabilities(Context("site", 220, 12), theta, {"season": 1.0})

    assert math.isclose(sum(early.values()), 1.0, abs_tol=1e-12)
    assert math.isclose(sum(late.values()), 1.0, abs_tol=1e-12)
    assert late["adult"] > early["adult"]
    assert late["dormant"] < early["dormant"]

    neutral = process.knockout().probabilities(
        Context("site", 220, 12), {}, {"season": 1.0}
    )
    assert all(math.isclose(value, 1 / 3, abs_tol=1e-12) for value in neutral.values())


def test_categorical_activity_is_normalized_and_uniform_knockout_is_no_effect():
    process = CategoricalActivityProcess(
        hours=(0, 6, 12, 18),
        reference_hour=0,
        covariates=("temperature",),
        intercept_parameters={6: "act_6", 12: "act_12", 18: "act_18"},
        coefficient_parameters={
            6: {"temperature": "act_6_temp"},
            12: {"temperature": "act_12_temp"},
            18: {"temperature": "act_18_temp"},
        },
    )
    theta = {
        "act_6": 0.0,
        "act_12": 1.2,
        "act_18": 0.2,
        "act_6_temp": 0.1,
        "act_12_temp": 0.5,
        "act_18_temp": -0.2,
    }
    probabilities = process.probabilities(theta, {"temperature": 1.0})
    assert math.isclose(sum(probabilities.values()), 1.0, abs_tol=1e-12)
    assert probabilities[12] == max(probabilities.values())

    neutral = process.knockout()
    neutral_probabilities = neutral.probabilities({}, {"temperature": 1.0})
    assert all(
        math.isclose(value, 0.25, abs_tol=1e-12)
        for value in neutral_probabilities.values()
    )
    for hour in process.hours:
        contribution = neutral.log_intensity_multiplier(
            Context("site", 100, hour), {}, {"temperature": 1.0}
        )
        assert math.isclose(contribution, 0.0, abs_tol=1e-12)
