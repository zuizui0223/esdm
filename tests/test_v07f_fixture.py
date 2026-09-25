import importlib.util

from esdm.process import ColonizationExtinctionOccupancy, StaticLinearOccupancy
from esdm.validate.v07f_fixture import (
    V07F_DYNAMIC_LIKE_TRUTH,
    V07F_STATIC_LIKE_TRUTH,
    build_v07f_fixture,
)
from esdm.validate.v07f_qualification import evaluate_v07f_identification


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_v07f_generators_are_out_of_candidate_family():
    fixture = build_v07f_fixture()

    dynamic_generator = next(
        process
        for process in fixture.dynamic_generator.species["sp"]
        if process.name == "occupancy"
    )
    dynamic_candidate = next(
        process
        for process in fixture.dynamic_training_model.species["sp"]
        if process.name == "occupancy"
    )
    assert isinstance(dynamic_generator, ColonizationExtinctionOccupancy)
    assert dynamic_generator.colonization_covariates == ("time",)
    assert dynamic_generator.extinction_covariates == ("time",)
    assert dynamic_candidate.colonization_covariates == ()
    assert dynamic_candidate.extinction_covariates == ()

    static_generator = next(
        process
        for process in fixture.static_generator.species["sp"]
        if process.name == "occupancy"
    )
    static_candidate = next(
        process
        for process in fixture.static_training_model.species["sp"]
        if process.name == "occupancy"
    )
    assert isinstance(static_generator, StaticLinearOccupancy)
    assert static_generator.covariates == ("time", "time2", "time3")
    assert static_candidate.covariates == ("time", "time2")


def test_v07f_candidates_remain_equal_dimension_and_observation_matched():
    fixture = build_v07f_fixture()

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


def test_v07f_truths_are_frozen_mild_misspecifications():
    assert V07F_DYNAMIC_LIKE_TRUTH["beta_gamma_time"] == 0.55
    assert V07F_DYNAMIC_LIKE_TRUTH["beta_epsilon_time"] == -0.35
    assert V07F_STATIC_LIKE_TRUTH["beta_time3"] == 0.35


def test_v07f_candidate_qualification_reuses_v07d_identifiability():
    if not JAX_AVAILABLE:
        return
    result = evaluate_v07f_identification()

    assert result.dynamic_structural_pass
    assert result.dynamic_practical_pass
    assert result.static_structural_pass
    assert result.static_practical_pass
