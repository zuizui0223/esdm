import math
import pytest

from esdm.simulate.misspecified import uniform_effort_intercept_bias


def test_effort_misspecification_is_visible_as_negative_control():
    bias = uniform_effort_intercept_bias(
        true_log_intensity=math.log(2.0),
        true_effort=(1.0, 1.0, 4.0, 4.0),
        assumed_effort=1.0,
    )
    assert bias > 0.5


def test_correct_mean_effort_removes_expected_intercept_bias():
    bias = uniform_effort_intercept_bias(
        true_log_intensity=math.log(2.0),
        true_effort=(1.0, 1.0, 4.0, 4.0),
        assumed_effort=2.5,
    )
    assert bias == pytest.approx(0.0)
