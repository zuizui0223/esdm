import pytest

from esdm.simulate import simulate_presence_only
from esdm.validate.field1_known_truth import (
    MODEL_IDS,
    PRIMARY_WORLD_IDS,
    field1_truth_theta,
    make_field1_fixture,
    make_field1_mean_covariance_factorial,
    make_field1_model,
    make_field1_primary_worlds,
    matched_barrier_distance_strata,
    subset_presence_data,
)


def test_field1_model_family_is_finite_and_design_informed():
    fixture = make_field1_fixture()
    for model_id in MODEL_IDS:
        model = make_field1_model(fixture, model_id)
        report = model.check_design()
        assert ("sp", "suitability") in report.informed_processes
        if model_id == "M0":
            assert ("sp", "spatial_field") not in report.informed_processes
        else:
            assert ("sp", "spatial_field") in report.informed_processes


def test_primary_worlds_freeze_truth_models_and_comparison_signs():
    worlds = make_field1_primary_worlds()
    assert tuple(world.world_id for world in worlds) == PRIMARY_WORLD_IDS
    assert tuple(world.truth_model_id for world in worlds) == MODEL_IDS

    by_id = {world.world_id: world for world in worlds}
    assert ("M1", "M0", "H1") in by_id["K1"].expected_positive_comparisons
    assert ("M2", "M1", "H1") in by_id["K2"].expected_positive_comparisons
    assert ("M3", "M1", "H2") in by_id["K3"].expected_positive_comparisons
    assert ("M4", "M2", "H2") in by_id["K4"].expected_positive_comparisons
    assert not by_id["K0"].expected_positive_comparisons


def test_k5_factorial_separates_environmental_mean_from_covariance_truth():
    worlds = make_field1_mean_covariance_factorial()
    assert len(worlds) == 4
    by_id = {world.world_id: world for world in worlds}

    assert by_id["K5_mean0_cov0"].mean_environment_beta == 0.0
    assert by_id["K5_mean1_cov0"].mean_environment_beta > 0.0
    assert by_id["K5_mean0_cov1"].truth_model_id == "M2"
    assert by_id["K5_mean1_cov1"].truth_model_id == "M2"

    for world_id in ("K5_mean0_cov0", "K5_mean1_cov0"):
        assert ("M2", "M1", "H1") in by_id[world_id].expected_null_comparisons
    for world_id in ("K5_mean0_cov1", "K5_mean1_cov1"):
        assert ("M2", "M1", "H1") in by_id[world_id].expected_positive_comparisons


def test_h1_h2_exposure_masks_are_complementary_and_response_free():
    fixture = make_field1_fixture()
    for holdout in ("H1", "H2"):
        training = fixture.training_spaces(holdout)
        heldout = fixture.heldout_spaces(holdout)
        assert training
        assert heldout
        assert set(training).isdisjoint(heldout)
        assert set(training) | set(heldout) == set(fixture.all_spaces)

        train_model = make_field1_model(
            fixture,
            "M4",
            domain_spaces=training,
        )
        heldout_model = make_field1_model(
            fixture,
            "M4",
            domain_spaces=heldout,
        )
        assert set(train_model.domain.space) == set(training)
        assert set(heldout_model.domain.space) == set(heldout)
        assert set(train_model.domain.space).isdisjoint(heldout_model.domain.space)


def test_k6_contains_distance_matched_barrier_and_nonbarrier_edges():
    strata = matched_barrier_distance_strata(make_field1_fixture())
    assert strata
    assert any(
        counts[0] > 0 and counts[1] > 0
        for counts in strata.values()
    )


def test_truth_theta_matches_each_model_parameter_surface():
    fixture = make_field1_fixture()
    for model_id in MODEL_IDS:
        model = make_field1_model(fixture, model_id)
        theta = field1_truth_theta(fixture, model_id)["sp"]
        expected = {
            parameter
            for process in model.species["sp"]
            for parameter in process.priors()
        }
        assert set(theta) == expected


def test_training_subset_drops_heldout_counts_instead_of_zero_coding_them():
    fixture = make_field1_fixture()
    truth_model = make_field1_model(fixture, "M4")
    theta = field1_truth_theta(fixture, "M4")
    generated = simulate_presence_only(
        truth_model,
        theta,
        fixture.covariates,
        seed=20260927,
    )

    training = fixture.training_spaces("H2")
    train_model = make_field1_model(
        fixture,
        "M4",
        domain_spaces=training,
    )
    subset = subset_presence_data(generated.counts, train_model)
    kept_spaces = {key[0] for key in subset["records"]["sp"]}

    assert kept_spaces == set(training)
    assert kept_spaces.isdisjoint(fixture.h2_heldout_spaces)
