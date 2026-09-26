import importlib.util

import pytest

from esdm.identify import IdentificationStatus
from esdm.validate.v07b_fixture import (
    V07B_HELDOUT_DOY,
    V07B_RECOVERY_TRUTH,
    V07B_TRAIN_DOY,
    build_v07b_fixture,
    full_trajectory_model,
    training_model,
)
from esdm.validate.v07b_qualification import evaluate_v07b_identification


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_v07b_split_is_exactly_eight_train_four_future_heldout():
    fixture = build_v07b_fixture()

    assert V07B_TRAIN_DOY == tuple(range(1, 9))
    assert V07B_HELDOUT_DOY == tuple(range(9, 13))
    assert [int(key[1]) for key in fixture.train_keys] == list(range(1, 9))
    assert [int(key[1]) for key in fixture.heldout_keys] == list(range(9, 13))


def test_v07b_direct_occupancy_exposure_is_zero_in_heldout_contexts():
    fixture = build_v07b_fixture()
    direct = next(
        stream
        for stream in fixture.base.positive_model.streams
        if stream.name == "occupancy_calibration"
    )
    mask = direct.structural_exposure_mask(fixture.base.positive_model.domain.keys)
    heldout_lookup = {
        key: exposed
        for key, exposed in zip(fixture.base.positive_model.domain.keys, mask)
        if key in fixture.heldout_keys
    }

    assert heldout_lookup
    assert not any(heldout_lookup.values())


def test_v07b_training_and_prediction_domains_do_not_reinitialize_heldout_trajectory():
    fixture = build_v07b_fixture()
    train, _ = training_model(fixture, knockout=False)
    full, _ = full_trajectory_model(fixture, knockout=False)

    assert tuple(train.domain.doy) == V07B_TRAIN_DOY
    assert tuple(full.domain.doy) == tuple(range(1, 13))
    assert all(key in full.domain.keys for key in fixture.heldout_keys)
    assert not any(key in train.domain.keys for key in fixture.heldout_keys)


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07b_training_split_remains_identified_and_joint_only_refused():
    result = evaluate_v07b_identification()

    assert result.positive_structural_pass
    assert result.positive_practical_pass
    assert result.joint_only_refusal_pass

    for target in V07B_RECOVERY_TRUTH:
        assert (
            result.positive_evidence[target].structural.status
            is IdentificationStatus.IDENTIFIED
        )
        assert result.positive_evidence[target].practical is not None
        assert result.positive_evidence[target].practical.target_sd_proxy <= 0.35
        assert (
            result.refusal_evidence[target].structural.status
            is IdentificationStatus.NOT_IDENTIFIED
        )
