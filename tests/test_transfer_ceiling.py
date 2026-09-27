import math

from esdm.transfer.ceiling import point_transfer_ceiling


def test_transfer_ceiling_reaches_final_level_when_all_groups_pass_every_step():
    result = point_transfer_ceiling(
        base_level="abiotic",
        ordered_steps=[("add_state", "state"), ("add_biotic", "biotic")],
        gains_by_step={"add_state": [0.2, 0.1], "add_biotic": [0.05, 0.08]},
    )
    assert result.level == "biotic"
    assert [step.status for step in result.steps] == ["pass", "pass"]


def test_later_positive_step_cannot_rescue_failed_earlier_step():
    result = point_transfer_ceiling(
        base_level="abiotic",
        ordered_steps=[("add_state", "state"), ("add_biotic", "biotic")],
        gains_by_step={"add_state": [0.2, -0.01], "add_biotic": [0.5, 0.5]},
    )
    assert result.level == "abiotic"
    assert result.steps[0].status == "fail"
    assert result.steps[1].status == "not_reached"


def test_transfer_ceiling_stops_at_first_failed_fine_level():
    result = point_transfer_ceiling(
        base_level="abiotic",
        ordered_steps=[("add_state", "state"), ("add_biotic", "biotic")],
        gains_by_step={"add_state": [0.2, 0.1], "add_biotic": [0.05, -0.01]},
    )
    assert result.level == "state"
    assert [step.status for step in result.steps] == ["pass", "fail"]


def test_nonfinite_gain_makes_step_unavailable_and_stops_ceiling():
    result = point_transfer_ceiling(
        base_level="abiotic",
        ordered_steps=[("add_state", "state")],
        gains_by_step={"add_state": [0.2, math.nan]},
    )
    assert result.level == "abiotic"
    assert result.steps[0].status == "unavailable"
