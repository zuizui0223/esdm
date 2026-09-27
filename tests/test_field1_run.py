import importlib.util
import sys

from types import SimpleNamespace

from esdm.validate.field1_known_truth import (
    field1_truth_theta,
    make_field1_fixture,
    make_field1_model,
    make_field1_primary_worlds,
    subset_presence_data,
)
from esdm.validate.field1_run import (
    FROZEN_FIELD1_MCMC_PROFILE,
    field1_required_fit_plan,
    run_field1_replicate,
)


NUMPYRO_AVAILABLE = (
    sys.version_info >= (3, 11)
    and importlib.util.find_spec("numpyro") is not None
)


def _prior_mean_fit(model, data, covariates, **kwargs):
    samples = {}
    for species, processes in model.species.items():
        for process in processes:
            for parameter, prior in process.priors().items():
                if prior.distribution == "Normal":
                    value = float(prior.parameters["loc"])
                elif prior.distribution == "HalfNormal":
                    # Deterministic positive stub value; this test exercises the
                    # frozen execution graph, not posterior accuracy.
                    value = float(prior.parameters["scale"])
                else:
                    raise AssertionError(
                        f"unsupported test prior {prior.distribution!r}"
                    )
                samples[f"{species}.{process.name}.{parameter}"] = [
                    value,
                    value,
                ]
    return SimpleNamespace(samples=samples, num_divergences=0)


def test_field1_frozen_mcmc_profile_inherits_r5b_profile():
    profile = FROZEN_FIELD1_MCMC_PROFILE
    assert profile.num_warmup == 300
    assert profile.num_samples == 350
    assert profile.num_chains == 2
    assert profile.target_accept_prob == 0.90


def test_field1_fit_plan_contains_each_required_fit_once():
    for world in make_field1_primary_worlds():
        plan = field1_required_fit_plan(world.world_id)
        assert len(plan) == len(set(plan))
        expected = {
            (holdout, model_id)
            for candidate, reference, holdout in (
                *world.expected_positive_comparisons,
                *world.expected_null_comparisons,
            )
            for model_id in (candidate, reference)
        }
        assert set(plan) == expected


def test_field1_replicate_runner_generates_once_and_scores_frozen_comparisons():
    result = run_field1_replicate(
        "K1",
        0,
        fit_fn=_prior_mean_fit,
    )
    world = {row.world_id: row for row in make_field1_primary_worlds()}["K1"]
    expected = {
        (candidate, reference, holdout)
        for candidate, reference, holdout in (
            *world.expected_positive_comparisons,
            *world.expected_null_comparisons,
        )
    }

    assert result.world_id == "K1"
    assert result.replicate == 0
    assert set(result.gains) == expected
    assert set(result.divergences) == set(field1_required_fit_plan("K1"))
    assert all(value == 0 for value in result.divergences.values())
    assert all(isinstance(value, float) for value in result.gains.values())



def test_field1_tiny_numpyro_fit_and_heldout_projection_smoke():
    if not NUMPYRO_AVAILABLE:
        return

    from esdm.model.backend_numpyro import fit_numpyro
    from esdm.simulate import simulate_presence_only
    from esdm.validate.evidence import poisson_log_predictive_density

    fixture = make_field1_fixture()
    truth_model = make_field1_model(fixture, "M1")
    generated = simulate_presence_only(
        truth_model,
        field1_truth_theta(fixture, "M1"),
        fixture.covariates,
        seed=91027,
    )

    training = fixture.training_spaces("H1")
    heldout = fixture.heldout_spaces("H1")
    train_model = make_field1_model(
        fixture,
        "M1",
        domain_spaces=training,
    )
    heldout_model = make_field1_model(
        fixture,
        "M1",
        domain_spaces=heldout,
    )
    fit = fit_numpyro(
        train_model,
        subset_presence_data(generated.counts, train_model),
        fixture.covariates,
        rng_seed=91028,
        num_warmup=10,
        num_samples=10,
        num_chains=1,
        progress_bar=False,
        target_accept_prob=0.8,
    )
    score = poisson_log_predictive_density(
        heldout_model,
        fit.samples,
        fixture.covariates,
        subset_presence_data(generated.counts, heldout_model),
        stream_name="records",
        species="sp",
    )

    assert isinstance(score, float)
    assert fit.num_divergences >= 0
    assert "sp.spatial_field.field_z_0000" in fit.samples
