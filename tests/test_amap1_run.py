from types import SimpleNamespace

from esdm.validate.amap1_known_truth import make_amap1_worlds
from esdm.validate.amap1_run import (
    FROZEN_AMAP1_MCMC_PROFILE,
    amap1_required_fit_plan,
    run_amap1_replicate,
)


def _prior_center_fit(model, data, covariates, **kwargs):
    samples = {}
    for species, processes in model.species.items():
        for process in processes:
            for parameter, prior in process.priors().items():
                if prior.distribution == "Normal":
                    value = float(prior.parameters["loc"])
                elif prior.distribution == "HalfNormal":
                    value = float(prior.parameters["scale"])
                elif prior.distribution == "Beta":
                    alpha = float(prior.parameters["alpha"])
                    beta = float(prior.parameters["beta"])
                    value = alpha / (alpha + beta)
                else:
                    raise AssertionError(
                        f"unsupported AMAP1 fake prior {prior.distribution!r}"
                    )
                samples[f"{species}.{process.name}.{parameter}"] = [
                    value,
                    value,
                ]
    return SimpleNamespace(samples=samples, num_divergences=0)


def test_amap1_mcmc_profile_is_frozen():
    profile = FROZEN_AMAP1_MCMC_PROFILE
    assert profile.num_warmup == 300
    assert profile.num_samples == 350
    assert profile.num_chains == 2
    assert profile.target_accept_prob == 0.90


def test_amap1_fit_plan_matches_truth_class():
    worlds = {world.world_id: world for world in make_amap1_worlds()}

    for world in worlds.values():
        plan = set(amap1_required_fit_plan(world.world_id))
        if world.truth_id == "T0":
            assert plan == {"B0", "BA"}
        elif world.truth_id == "TX":
            assert plan == {"B0", "BA", "BX"}
        elif world.truth_id == "TC":
            assert plan == {"B0", "BA", "BC"}
        else:
            raise AssertionError(world.truth_id)


def test_amap1_frozen_total_fit_count_is_384():
    total = sum(
        len(amap1_required_fit_plan(world.world_id)) * 16
        for world in make_amap1_worlds()
    )
    assert total == 384


def test_amap1_replicate_runner_scores_regret_and_detectability():
    tx = run_amap1_replicate(
        "G1_TX",
        0,
        fit_fn=_prior_center_fit,
    )
    assert tx.world_id == "G1_TX"
    assert tx.replicate == 0
    assert isinstance(tx.regret, float)
    assert isinstance(tx.detectability_gain, float)
    assert set(tx.divergences) == {"B0", "BA", "BX"}
    assert all(value == 0 for value in tx.divergences.values())

    t0 = run_amap1_replicate(
        "G2_T0",
        1,
        fit_fn=_prior_center_fit,
    )
    assert isinstance(t0.regret, float)
    assert t0.detectability_gain is None
    assert set(t0.divergences) == {"B0", "BA"}


def test_amap1_replicate_runner_is_deterministic_for_fixed_seed_and_stub():
    first = run_amap1_replicate(
        "G3_TC",
        2,
        fit_fn=_prior_center_fit,
    )
    second = run_amap1_replicate(
        "G3_TC",
        2,
        fit_fn=_prior_center_fit,
    )

    assert first.regret == second.regret
    assert first.detectability_gain == second.detectability_gain
    assert dict(first.divergences) == dict(second.divergences)
