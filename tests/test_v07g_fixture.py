from itertools import combinations

from esdm.validate.v07g_fixture import (
    V07G_BASELINE_PLACEMENT,
    V07G_CALIBRATION_COUNT,
    V07G_TOTAL_DIRECT_EFFORT,
    build_v07g_fixture,
)


def test_v07g_enumerates_seventy_budget_matched_placements():
    placements = tuple(combinations(range(1, 9), V07G_CALIBRATION_COUNT))

    assert len(placements) == 70
    assert V07G_BASELINE_PLACEMENT in placements

    for placement in placements:
        fixture = build_v07g_fixture(placement)
        assert fixture.placement == placement
        assert fixture.total_direct_effort == V07G_TOTAL_DIRECT_EFFORT


def test_v07g_direct_calibration_never_leaks_into_heldout_contexts():
    fixture = build_v07g_fixture((1, 3, 5, 7))
    direct = next(
        stream
        for stream in fixture.training_model.streams
        if stream.name == "occupancy_calibration"
    )
    mask = direct.structural_exposure_mask(
        fixture.training_model.domain.keys
    )

    heldout = set(fixture.source.heldout_keys)
    assert not any(
        exposed
        for key, exposed in zip(
            fixture.training_model.domain.keys,
            mask,
            strict=True,
        )
        if key in heldout
    )


def test_v07g_baseline_is_the_frozen_early_four_design():
    fixture = build_v07g_fixture(V07G_BASELINE_PLACEMENT)

    assert fixture.placement == (1, 2, 3, 4)
    assert fixture.total_direct_effort == 2000.0


def test_v07g_validation_fixture_pairs_same_budget_designs():
    from esdm.validate.v07g_fixture import (
        V07G_BASELINE_PLACEMENT,
        V07G_SELECTED_PLACEMENT,
        build_v07g_validation_fixture,
    )

    fixture = build_v07g_validation_fixture()

    assert V07G_SELECTED_PLACEMENT == (2, 6, 7, 8)
    assert V07G_BASELINE_PLACEMENT == (1, 2, 3, 4)
    assert tuple(key[1] for key in fixture.optimized_keys) == V07G_SELECTED_PLACEMENT
    assert tuple(key[1] for key in fixture.baseline_keys) == V07G_BASELINE_PLACEMENT

    generator_direct = next(
        stream
        for stream in fixture.generator_model.streams
        if stream.name == "occupancy_calibration"
    )
    mask = generator_direct.structural_exposure_mask(
        fixture.generator_model.domain.keys
    )
    exposed_days = tuple(
        key[1]
        for key, exposed in zip(
            fixture.generator_model.domain.keys,
            mask,
            strict=True,
        )
        if exposed
    )
    assert exposed_days == tuple(range(1, 9))
