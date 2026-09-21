import math

import pytest


def test_spatial_maximin_starts_farthest_and_breaks_ties_by_id():
    from esdm.validate.v04_r3a_design import spatial_maximin_sequence

    spaces = ("b", "a", "c", "d")
    covariates = {
        ("a", 15, 0): {"precip_z_train": 2.0, "eastness_z_train": 0.0},
        ("b", 15, 0): {"precip_z_train": -2.0, "eastness_z_train": 0.0},
        ("c", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": 1.0},
        ("d", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": -1.0},
    }

    selected = spatial_maximin_sequence(spaces, covariates, count=4)

    assert selected[0] == "a"
    assert set(selected) == set(spaces)
    assert len(selected) == len(set(selected)) == 4


def test_spatial_maximin_repeated_calls_are_exactly_equal():
    from esdm.validate.v04_r3a_design import spatial_maximin_sequence

    spaces = ("a", "b", "c", "d", "e")
    covariates = {
        ("a", 15, 0): {"precip_z_train": 2.0, "eastness_z_train": 0.0},
        ("b", 15, 0): {"precip_z_train": -2.0, "eastness_z_train": 0.0},
        ("c", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": 1.0},
        ("d", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": -1.0},
        ("e", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": 0.0},
    }

    assert spatial_maximin_sequence(
        spaces,
        covariates,
        count=5,
    ) == spatial_maximin_sequence(
        spaces,
        covariates,
        count=5,
    )


@pytest.mark.parametrize("count", [0, 5])
def test_spatial_maximin_rejects_invalid_count(count):
    from esdm.validate.v04_r3a_design import spatial_maximin_sequence

    spaces = ("a", "b", "c", "d")
    covariates = {
        (space, 15, 0): {
            "precip_z_train": float(index),
            "eastness_z_train": 0.0,
        }
        for index, space in enumerate(spaces)
    }

    with pytest.raises(ValueError, match="spatial"):
        spatial_maximin_sequence(spaces, covariates, count=count)


def test_spatial_maximin_rejects_duplicate_spaces():
    from esdm.validate.v04_r3a_design import spatial_maximin_sequence

    covariates = {
        ("a", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": 0.0},
    }

    with pytest.raises(ValueError, match="unique"):
        spatial_maximin_sequence(("a", "a"), covariates, count=1)


@pytest.mark.parametrize(
    ("values", "missing"),
    [
        ({"eastness_z_train": 0.0}, "precip_z_train"),
        ({"precip_z_train": 0.0}, "eastness_z_train"),
    ],
)
def test_spatial_maximin_rejects_missing_declared_coordinate(values, missing):
    from esdm.validate.v04_r3a_design import spatial_maximin_sequence

    with pytest.raises(KeyError, match=missing):
        spatial_maximin_sequence(
            ("a",),
            {("a", 15, 0): values},
            count=1,
        )


@pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
def test_spatial_maximin_rejects_nonfinite_coordinates(bad):
    from esdm.validate.v04_r3a_design import spatial_maximin_sequence

    with pytest.raises(ValueError, match="finite"):
        spatial_maximin_sequence(
            ("a",),
            {
                ("a", 15, 0): {
                    "precip_z_train": bad,
                    "eastness_z_train": 0.0,
                }
            },
            count=1,
        )


def test_temporal_maximin_is_deterministic_and_starts_at_15_0():
    from esdm.validate.v04_r3a_design import temporal_maximin_sequence

    selected = temporal_maximin_sequence(
        (15, 75, 135, 195, 255, 315),
        (0, 6, 12, 18),
        count=12,
    )

    assert selected[0] == (15, 0)
    assert len(selected) == 12
    assert len(set(selected)) == 12
    assert set(selected) <= {
        (doy, hour)
        for doy in (15, 75, 135, 195, 255, 315)
        for hour in (0, 6, 12, 18)
    }


def test_temporal_maximin_repeated_calls_are_exactly_equal():
    from esdm.validate.v04_r3a_design import temporal_maximin_sequence

    args = (
        (15, 75, 135, 195, 255, 315),
        (0, 6, 12, 18),
    )
    first = temporal_maximin_sequence(*args, count=12)
    second = temporal_maximin_sequence(*args, count=12)

    assert first == second


def test_temporal_maximin_breaks_equal_distance_ties_lexicographically():
    from esdm.validate.v04_r3a_design import temporal_maximin_sequence

    selected = temporal_maximin_sequence((15,), (0, 6, 18), count=2)

    assert selected == ((15, 0), (15, 6))


@pytest.mark.parametrize("count", [0, 25])
def test_temporal_maximin_rejects_invalid_count(count):
    from esdm.validate.v04_r3a_design import temporal_maximin_sequence

    with pytest.raises(ValueError, match="temporal"):
        temporal_maximin_sequence(
            (15, 75, 135, 195, 255, 315),
            (0, 6, 12, 18),
            count=count,
        )


def test_temporal_maximin_rejects_duplicate_candidates():
    from esdm.validate.v04_r3a_design import temporal_maximin_sequence

    with pytest.raises(ValueError, match="unique"):
        temporal_maximin_sequence((15, 15), (0,), count=1)
