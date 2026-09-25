import pytest

from esdm.validate.v07h_fixture import (
    V07H_BASELINE_EXPECTED_DIRECT_COUNT,
    V07H_BASELINE_TOTAL_EFFORT,
    V07H_SELECTED_TOTAL_EFFORT,
    build_v07h_fixture,
    expected_direct_count,
)


def test_v07h_expected_direct_counts_are_matched():
    fixture = build_v07h_fixture()

    baseline = expected_direct_count(fixture.baseline_model, fixture)
    selected = expected_direct_count(fixture.selected_model, fixture)

    assert baseline == pytest.approx(V07H_BASELINE_EXPECTED_DIRECT_COUNT)
    assert selected == pytest.approx(baseline, rel=1e-12, abs=1e-12)


def test_v07h_selected_design_uses_less_field_effort_after_count_matching():
    assert V07H_SELECTED_TOTAL_EFFORT < V07H_BASELINE_TOTAL_EFFORT
    assert V07H_SELECTED_TOTAL_EFFORT / V07H_BASELINE_TOTAL_EFFORT == pytest.approx(
        0.7383090740167234
    )


def test_v07h_candidate_placements_remain_frozen():
    fixture = build_v07h_fixture()

    assert tuple(key[1] for key in fixture.selected_keys) == (2, 6, 7, 8)
    assert tuple(key[1] for key in fixture.baseline_keys) == (1, 2, 3, 4)
