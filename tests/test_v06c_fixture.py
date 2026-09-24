import pytest


def test_v06c_expected_auxiliary_record_budgets_match():
    from esdm.validate.v06c_fixture import (
        V06C_MATCHED_JOINT_EFFORT,
        build_v06c_fixture,
    )

    fixture = build_v06c_fixture()
    assert V06C_MATCHED_JOINT_EFFORT == pytest.approx(
        12.168687798294679
    )
    assert fixture.relative_budget_error <= 1e-12
    assert fixture.expected_direct_aux_count == pytest.approx(
        fixture.expected_matched_aux_count,
        rel=1e-12,
        abs=1e-12,
    )


def test_v06c_auxiliary_streams_have_zero_heldout_exposure():
    from esdm.validate.v06c_fixture import build_v06c_fixture

    fixture = build_v06c_fixture()
    streams = {stream.name: stream for stream in fixture.model.streams}
    heldout = set(fixture.heldout_spaces)

    for name in ("direct_access", "matched_joint"):
        assert all(
            streams[name].effort.at(key) == 0.0
            for key in fixture.model.domain.keys
            if key[0] in heldout
        )
