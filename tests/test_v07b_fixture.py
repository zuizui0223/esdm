import importlib.util

import pytest

from esdm.identify import IdentificationStatus
from esdm.simulate import simulate_observations
from esdm.validate.v07b_fixture import (
    V07B_DIRECT_TRAIN_COUNT,
    V07B_HELDOUT_COUNT,
    V07B_JOINT_TRAIN_COUNT,
    V07B_TRUTH,
    build_v07b_fixture,
)
from esdm.validate.v07b_run import _training_data


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_v07b_temporal_exposure_is_strictly_nested_and_disjoint():
    fixture = build_v07b_fixture()
    keys = tuple(fixture.training_model.domain.keys)
    joint = next(
        stream for stream in fixture.training_model.streams
        if stream.name == "joint"
    )
    direct = next(
        stream for stream in fixture.training_model.streams
        if stream.name == "occupancy_calibration"
    )

    assert len(fixture.joint_train_keys) == V07B_JOINT_TRAIN_COUNT
    assert len(fixture.direct_train_keys) == V07B_DIRECT_TRAIN_COUNT
    assert len(fixture.heldout_keys) == V07B_HELDOUT_COUNT
    assert set(fixture.direct_train_keys).issubset(
        set(fixture.joint_train_keys)
    )
    assert not (
        set(fixture.joint_train_keys) & set(fixture.heldout_keys)
    )

    joint_mask = joint.structural_exposure_mask(keys)
    direct_mask = direct.structural_exposure_mask(keys)
    assert sum(joint_mask) == V07B_JOINT_TRAIN_COUNT
    assert sum(direct_mask) == V07B_DIRECT_TRAIN_COUNT
    assert not any(
        direct_mask[keys.index(key)]
        for key in fixture.heldout_keys
    )


def test_v07b_training_data_never_contains_heldout_counts():
    fixture = build_v07b_fixture()
    generated = simulate_observations(
        fixture.generator_model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=11,
    )
    train = _training_data(generated.counts, fixture)

    assert set(train["joint"]["sp"]) == set(fixture.joint_train_keys)
    assert set(train["occupancy_calibration"]["sp"]) == set(
        fixture.direct_train_keys
    )
    assert not (
        set(train["joint"]["sp"]) & set(fixture.heldout_keys)
    )
    assert not (
        set(train["occupancy_calibration"]["sp"])
        & set(fixture.heldout_keys)
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07b_training_design_qualifies_before_mcmc():
    from esdm.validate.v07b_qualification import evaluate_v07b_identification

    result = evaluate_v07b_identification()

    assert result.joint_only_refusal_pass
    assert result.positive_structural_pass
    assert result.positive_practical_pass
    for target in V07B_TRUTH:
        assert (
            result.refusal_evidence[target].structural.status
            is IdentificationStatus.NOT_IDENTIFIED
        )
        assert (
            result.positive_evidence[target].structural.status
            is IdentificationStatus.IDENTIFIED
        )
        practical = result.positive_evidence[target].practical
        assert practical is not None
        assert practical.target_sd_proxy <= 0.25
