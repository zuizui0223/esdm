import importlib.util

from esdm.validate.v07k_fixture import theta_for_v07k_world
from esdm.validate.v07k_fixture import (
    V07K_ORACLE_PLACEMENTS,
    V07K_TOTAL_DIRECT_EFFORT,
    V07K_TRANSFERRED_PLACEMENT,
    V07K_WORLDS,
    build_v07k_confirm_fixture,
    build_v07k_local_pilot_fixture,
)


def _effort(stream, keys):
    return sum(
        float(stream.effort.at(key, theta={}, covariates={}))
        for key in keys
    )


def test_v07k_local_pilot_uses_shifted_world_truth():
    for world in V07K_WORLDS:
        fixture = build_v07k_local_pilot_fixture(world)

        assert fixture.generating_theta == theta_for_v07k_world(world)
        assert len(fixture.pilot_keys) == 4
        assert fixture.world == world


def test_v07k_confirmatory_candidates_match_field_effort_and_joint_stream():
    for world in V07K_WORLDS:
        fixture = build_v07k_confirm_fixture(
            world,
            V07K_ORACLE_PLACEMENTS[world],
        )
        adaptive = next(
            stream for stream in fixture.adaptive_model.streams
            if stream.name == "adaptive_calibration"
        )
        transferred = next(
            stream for stream in fixture.transferred_model.streams
            if stream.name == "transferred_calibration"
        )
        assert _effort(
            adaptive, fixture.adaptive_model.domain.keys
        ) == V07K_TOTAL_DIRECT_EFFORT
        assert _effort(
            transferred, fixture.transferred_model.domain.keys
        ) == V07K_TOTAL_DIRECT_EFFORT

        adaptive_joint = next(
            stream for stream in fixture.adaptive_model.streams
            if stream.name == "joint"
        )
        transferred_joint = next(
            stream for stream in fixture.transferred_model.streams
            if stream.name == "joint"
        )
        assert adaptive_joint == transferred_joint

        heldout = set(fixture.heldout_keys)
        for stream, model in (
            (adaptive, fixture.adaptive_model),
            (transferred, fixture.transferred_model),
        ):
            mask = stream.structural_exposure_mask(model.domain.keys)
            assert not any(
                exposed
                for key, exposed in zip(model.domain.keys, mask, strict=True)
                if key in heldout
            )


def test_v07k_transferred_schedule_is_frozen_v07i_schedule():
    assert V07K_TRANSFERRED_PLACEMENT == (2, 6, 7, 8)
