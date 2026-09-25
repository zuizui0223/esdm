import importlib.util

import pytest

from esdm.validate.v07c_fixture import build_v07c_fixture
from esdm.validate.v07c_qualification import evaluate_v07c_identification


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_v07c_models_share_observation_budget_and_future_holdout():
    fixture = build_v07c_fixture()

    assert fixture.dynamic_training_model.streams == fixture.static_training_model.streams
    assert fixture.dynamic_scoring_model.streams == fixture.static_scoring_model.streams
    assert len(fixture.joint_train_keys) == 8
    assert len(fixture.direct_train_keys) == 4
    assert len(fixture.heldout_keys) == 4
    assert not set(fixture.joint_train_keys) & set(fixture.heldout_keys)
    assert set(fixture.direct_train_keys).issubset(set(fixture.joint_train_keys))

    direct = next(
        stream
        for stream in fixture.static_training_model.streams
        if stream.name == "occupancy_calibration"
    )
    mask = direct.structural_exposure_mask(
        fixture.static_training_model.domain.keys
    )
    assert sum(mask) == 4
    assert not any(
        exposed
        for key, exposed in zip(
            fixture.static_training_model.domain.keys,
            mask,
            strict=True,
        )
        if key in set(fixture.heldout_keys)
    )


def test_v07c_static_model_is_memoryless_and_lower_dimensional():
    fixture = build_v07c_fixture()
    dynamic_parameters = sum(
        len(process.priors())
        for process in fixture.dynamic_training_model.species["sp"]
    )
    static_parameters = sum(
        len(process.priors())
        for process in fixture.static_training_model.species["sp"]
    )

    assert dynamic_parameters == 4
    assert static_parameters == 3

    time_values = [
        fixture.covariates[key]["time"]
        for key in fixture.static_training_model.domain.keys
    ]
    assert time_values[0] == pytest.approx(-1.0)
    assert time_values[-1] == pytest.approx(1.0)
    assert all(
        left < right
        for left, right in zip(time_values, time_values[1:])
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07c_both_models_are_structurally_and_practically_estimable():
    result = evaluate_v07c_identification()

    assert result.dynamic_structural_pass
    assert result.dynamic_practical_pass
    assert result.static_structural_pass
    assert result.static_practical_pass
