import importlib.util
import sys
from types import SimpleNamespace

from esdm.validate.map1_known_truth import (
    make_map1_fixture,
    make_map1_model,
    make_map1_worlds,
    map1_truth_theta,
    subset_map1_data,
)
from esdm.validate.map1_run import (
    FROZEN_MAP1_MCMC_PROFILE,
    map1_required_fit_plan,
    run_map1_replicate,
)


NUMPYRO_AVAILABLE = (
    sys.version_info >= (3, 11)
    and importlib.util.find_spec("numpyro") is not None
)


def _fake_fit(model, data, covariates, **kwargs):
    samples = {}
    for species, processes in model.species.items():
        for process in processes:
            for parameter, prior in process.priors().items():
                if prior.distribution == "Normal":
                    value = float(prior.parameters["loc"])
                elif prior.distribution == "HalfNormal":
                    value = float(prior.parameters["scale"])
                else:
                    raise AssertionError(prior.distribution)
                samples[f"{species}.{process.name}.{parameter}"] = [value, value]
    return SimpleNamespace(samples=samples, num_divergences=0)


def test_map1_frozen_mcmc_profile():
    profile = FROZEN_MAP1_MCMC_PROFILE
    assert profile.num_warmup == 300
    assert profile.num_samples == 350
    assert profile.num_chains == 2
    assert profile.target_accept_prob == 0.90


def test_map1_fit_plans_are_finite_and_total_128():
    total = 0
    for world in make_map1_worlds():
        plan = map1_required_fit_plan(world.world_id)
        assert len(plan) == len(set(plan))
        total += len(plan) * 16
    assert total == 128


def test_map1_replicate_runner_scores_declared_comparisons_only():
    result = run_map1_replicate("P1", 0, fit_fn=_fake_fit)
    world = {row.world_id: row for row in make_map1_worlds()}["P1"]
    expected = {
        (candidate, reference, holdout)
        for candidate, reference, holdout in (
            *world.expected_positive_comparisons,
            *world.expected_null_comparisons,
        )
    }
    assert set(result.gains) == expected
    assert set(result.divergences) == set(map1_required_fit_plan("P1"))
    assert all(value == 0 for value in result.divergences.values())


def test_map1_tiny_numpyro_train_to_heldout_smoke():
    if not NUMPYRO_AVAILABLE:
        return

    from esdm.model.backend_numpyro import fit_numpyro
    from esdm.simulate import simulate_presence_only
    from esdm.validate.evidence import poisson_log_predictive_density

    fixture = make_map1_fixture()
    truth = make_map1_model(fixture, "BC")
    generated = simulate_presence_only(
        truth,
        map1_truth_theta(fixture, "BC", innovation_seed=991),
        fixture.covariates,
        seed=992,
    )
    train = make_map1_model(
        fixture,
        "BC",
        domain_spaces=fixture.training_spaces(),
    )
    heldout = make_map1_model(
        fixture,
        "BC",
        domain_spaces=fixture.heldout_spaces(),
    )
    fit = fit_numpyro(
        train,
        subset_map1_data(generated.counts, train),
        fixture.covariates,
        rng_seed=993,
        num_warmup=10,
        num_samples=10,
        num_chains=1,
        progress_bar=False,
        target_accept_prob=0.8,
    )
    score = poisson_log_predictive_density(
        heldout,
        fit.samples,
        fixture.covariates,
        subset_map1_data(generated.counts, heldout),
        stream_name="records",
        species="sp",
    )
    assert isinstance(score, float)
    assert "sp.map_coherence.map_sigma" in fit.samples
