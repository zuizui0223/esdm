import pytest


def test_v06c_alignment_constructor_hits_frozen_correlations():
    from esdm.validate.v06c_alignment_audit import (
        V06C_ALIGNMENTS,
        _aligned_covariates,
    )

    for rho in V06C_ALIGNMENTS:
        _grid, _covariates, correlation = _aligned_covariates(rho)
        assert correlation == pytest.approx(rho, abs=1e-10)


def test_v06c_compares_joint_only_with_direct_calibration():
    from esdm.validate.v06c_alignment_audit import _models

    joint, calibrated, _cov, _theta, joint_obs, direct_obs, _corr = _models(0.5)

    assert tuple(stream.name for stream in joint.streams) == ("joint",)
    assert tuple(stream.name for stream in calibrated.streams) == ("joint", "access")
    assert joint_obs == {"joint": {}}
    assert direct_obs == {"joint": {}, "access": {}}
