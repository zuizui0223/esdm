import importlib.util

import pytest

from esdm.validate.v07d_fixture import build_v07d_fixture
from esdm.validate.v07d_qualification import evaluate_v07d_identification


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_v07d_is_exactly_equal_dimension():
    fixture = build_v07d_fixture()

    dynamic_parameters = sum(
        len(process.priors())
        for process in fixture.dynamic_training_model.species["sp"]
    )
    static_parameters = sum(
        len(process.priors())
        for process in fixture.static_training_model.species["sp"]
    )

    assert dynamic_parameters == 4
    assert static_parameters == 4


def test_v07d_models_share_identical_observation_programme():
    fixture = build_v07d_fixture()

    assert fixture.dynamic_training_model.streams == fixture.static_training_model.streams
    assert fixture.dynamic_scoring_model.streams == fixture.static_scoring_model.streams
    assert len(fixture.joint_train_keys) == 8
    assert len(fixture.direct_train_keys) == 4
    assert len(fixture.heldout_keys) == 4
    assert not set(fixture.joint_train_keys) & set(fixture.heldout_keys)
    assert set(fixture.direct_train_keys).issubset(set(fixture.joint_train_keys))


def test_v07d_static_comparator_has_linear_and_quadratic_time_terms():
    fixture = build_v07d_fixture()
    process = next(
        process
        for process in fixture.static_training_model.species["sp"]
        if process.name == "occupancy"
    )

    assert process.covariates == ("time", "time2")
    assert process.coefficient_parameters["time"] == "beta_time"
    assert process.coefficient_parameters["time2"] == "beta_time2"

    for key in fixture.static_training_model.domain.keys:
        time = fixture.covariates[key]["time"]
        assert fixture.covariates[key]["time2"] == pytest.approx(time * time)


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_v07d_both_equal_dimension_models_are_estimable():
    result = evaluate_v07d_identification()

    assert result.dynamic_structural_pass
    assert result.dynamic_practical_pass
    assert result.static_structural_pass
    assert result.static_practical_pass
