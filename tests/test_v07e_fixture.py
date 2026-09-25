import importlib.util

from esdm.process import ColonizationExtinctionOccupancy, StaticLinearOccupancy
from esdm.validate.v07e_fixture import build_v07e_fixture
from esdm.validate.v07e_qualification import evaluate_v07e_identification


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_v07e_generator_is_static_quadratic_not_recursive():
    fixture = build_v07e_fixture()
    occupancy = next(
        process
        for process in fixture.generator_model.species["sp"]
        if process.name == "occupancy"
    )

    assert isinstance(occupancy, StaticLinearOccupancy)
    assert not isinstance(occupancy, ColonizationExtinctionOccupancy)
    assert occupancy.covariates == ("time", "time2")


def test_v07e_keeps_equal_dimension_models_and_same_observation_programme():
    fixture = build_v07e_fixture()

    dynamic_count = sum(
        len(process.priors())
        for process in fixture.dynamic_training_model.species["sp"]
    )
    static_count = sum(
        len(process.priors())
        for process in fixture.static_training_model.species["sp"]
    )
    assert dynamic_count == static_count == 4

    assert fixture.dynamic_training_model.streams == fixture.static_training_model.streams
    assert fixture.dynamic_scoring_model.streams == fixture.static_scoring_model.streams
    assert len(fixture.joint_train_keys) == 8
    assert len(fixture.direct_train_keys) == 4
    assert len(fixture.heldout_keys) == 4
    assert not set(fixture.joint_train_keys) & set(fixture.heldout_keys)
    assert set(fixture.direct_train_keys).issubset(set(fixture.joint_train_keys))


def test_v07e_static_generator_uses_frozen_v07d_nominal_truth():
    fixture = build_v07e_fixture()
    theta = fixture.generating_theta["sp"]

    assert theta["alpha"] == 0.30
    assert theta["occupancy_intercept"] == -0.50
    assert theta["beta_time"] == 1.50
    assert theta["beta_time2"] == 0.25


def test_v07e_qualification_reuses_estimable_equal_dimension_candidates():
    if not JAX_AVAILABLE:
        return
    result = evaluate_v07e_identification()

    assert result.dynamic_structural_pass
    assert result.dynamic_practical_pass
    assert result.static_structural_pass
    assert result.static_practical_pass
