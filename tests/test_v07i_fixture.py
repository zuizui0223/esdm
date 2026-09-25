import importlib.util

import pytest

from esdm.validate.v07g_fixture import V07G_SELECTED_PLACEMENT
from esdm.validate.v07i_fixture import (
    V07I_PILOT_PLACEMENT,
    V07I_TOTAL_DIRECT_EFFORT,
    build_v07i_confirm_fixture,
    build_v07i_pilot_fixture,
)
from esdm.validate.v07i_selector import select_v07i_placement_from_theta


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _direct_effort(stream, keys):
    return sum(
        float(stream.effort.at(key, theta={}, covariates={}))
        for key in keys
    )


def test_v07i_pilot_is_early_four_and_has_no_heldout_direct_exposure():
    fixture = build_v07i_pilot_fixture()

    assert V07I_PILOT_PLACEMENT == (1, 2, 3, 4)
    assert len(fixture.pilot_keys) == 4
    direct = next(
        stream
        for stream in fixture.training_model.streams
        if stream.name == "pilot_calibration"
    )
    assert _direct_effort(
        direct, fixture.training_model.domain.keys
    ) == V07I_TOTAL_DIRECT_EFFORT

    heldout = set(fixture.source.heldout_keys)
    mask = direct.structural_exposure_mask(fixture.training_model.domain.keys)
    assert not any(
        exposed
        for key, exposed in zip(
            fixture.training_model.domain.keys,
            mask,
            strict=True,
        )
        if key in heldout
    )


def test_v07i_confirm_candidates_have_equal_field_effort_and_shared_joint_stream():
    fixture = build_v07i_confirm_fixture((2, 6, 7, 8))

    assert fixture.selected_placement == (2, 6, 7, 8)
    selected_direct = next(
        stream
        for stream in fixture.selected_model.streams
        if stream.name == "selected_calibration"
    )
    baseline_direct = next(
        stream
        for stream in fixture.baseline_model.streams
        if stream.name == "baseline_calibration"
    )
    assert _direct_effort(
        selected_direct, fixture.selected_model.domain.keys
    ) == V07I_TOTAL_DIRECT_EFFORT
    assert _direct_effort(
        baseline_direct, fixture.baseline_model.domain.keys
    ) == V07I_TOTAL_DIRECT_EFFORT

    selected_joint = next(
        stream for stream in fixture.selected_model.streams
        if stream.name == "joint"
    )
    baseline_joint = next(
        stream for stream in fixture.baseline_model.streams
        if stream.name == "joint"
    )
    assert selected_joint == baseline_joint


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07i_selector_recovers_v07g_oracle_at_frozen_truth():
    pilot = build_v07i_pilot_fixture()

    selection = select_v07i_placement_from_theta(
        pilot.generating_theta
    )

    assert selection.placements_evaluated == 70
    assert selection.selected.placement == V07G_SELECTED_PLACEMENT
    assert selection.selected_to_baseline_predicted_ratio < 0.70
