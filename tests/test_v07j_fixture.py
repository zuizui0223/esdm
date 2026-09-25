import math

from esdm.validate.v07g_fixture import (
    V07G_BASELINE_PLACEMENT,
    V07G_SELECTED_PLACEMENT,
)
from esdm.validate.v07j_fixture import (
    V07J_TARGET_WORLDS,
    V07J_WORLD_ORDER,
    build_v07j_fixture,
    truth_sites,
)


def _logit(p):
    return math.log(p / (1.0 - p))


def test_v07j_target_worlds_are_exactly_frozen_three():
    assert V07J_WORLD_ORDER == (
        "low_occupancy",
        "high_occupancy",
        "high_turnover",
    )
    assert V07J_TARGET_WORLDS == {
        "low_occupancy": {
            "alpha": 0.30,
            "psi0": 0.10,
            "gamma": 0.20,
            "epsilon": 0.30,
        },
        "high_occupancy": {
            "alpha": 0.30,
            "psi0": 0.50,
            "gamma": 0.55,
            "epsilon": 0.10,
        },
        "high_turnover": {
            "alpha": 0.30,
            "psi0": 0.20,
            "gamma": 0.55,
            "epsilon": 0.40,
        },
    }


def test_v07j_truth_sites_encode_shifted_probabilities_on_logit_scale():
    low = truth_sites("low_occupancy")
    assert low["sp.suitability.alpha"] == 0.30
    assert low["sp.occupancy.psi0_logit"] == _logit(0.10)
    assert low["sp.occupancy.gamma_logit"] == _logit(0.20)
    assert low["sp.occupancy.epsilon_logit"] == _logit(0.30)


def test_v07j_keeps_v07i_deployed_schedule_and_early_four_baseline():
    assert V07G_SELECTED_PLACEMENT == (2, 6, 7, 8)
    assert V07G_BASELINE_PLACEMENT == (1, 2, 3, 4)

    fixture = build_v07j_fixture("high_turnover")
    selected_days = tuple(sorted(int(key[1]) for key in fixture.selected_keys))
    baseline_days = tuple(sorted(int(key[1]) for key in fixture.baseline_keys))

    assert selected_days == V07G_SELECTED_PLACEMENT
    assert baseline_days == V07G_BASELINE_PLACEMENT
    assert all(int(key[1]) >= 9 for key in fixture.heldout_keys)


def test_v07j_changes_generator_truth_not_model_or_score_semantics():
    low = build_v07j_fixture("low_occupancy")
    high = build_v07j_fixture("high_occupancy")

    assert low.generator_model == high.generator_model
    assert low.selected_model == high.selected_model
    assert low.baseline_model == high.baseline_model
    assert low.scoring_model == high.scoring_model
    assert low.covariates == high.covariates
    assert low.generating_theta != high.generating_theta
