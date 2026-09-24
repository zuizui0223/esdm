import pytest


def test_v06c_frontier_grid_is_exactly_three_by_three():
    from esdm.validate.v06c_frontier import (
        V06C_ACCESS_INTERCEPTS,
        V06C_GEOMETRIES,
        _models,
    )

    assert V06C_GEOMETRIES == ("distinct", "aligned", "flat_access")
    assert V06C_ACCESS_INTERCEPTS == (-2.0, 0.40, 2.0)

    for geometry in V06C_GEOMETRIES:
        for intercept in V06C_ACCESS_INTERCEPTS:
            joint, direct, cov, theta, joint_obs, direct_obs = _models(
                geometry, intercept
            )
            assert tuple(stream.name for stream in joint.streams) == ("joint",)
            assert tuple(stream.name for stream in direct.streams) == (
                "joint",
                "access",
            )
            assert theta["sp"]["access_intercept"] == pytest.approx(intercept)
            assert joint_obs == {"joint": {}}
            assert direct_obs == {"joint": {}, "access": {}}
            assert len(cov) == 24


def test_v06c_aligned_and_flat_geometries_are_literal():
    from esdm.validate.v06c_frontier import _covariates

    _grid, aligned = _covariates("aligned")
    assert all(
        values["distance"] == pytest.approx(values["habitat"])
        for values in aligned.values()
    )

    _grid, flat = _covariates("flat_access")
    assert all(values["distance"] == 0.0 for values in flat.values())
