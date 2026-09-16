import importlib.util
import math

import pytest

from esdm.validate.v031_knockout import (
    V031KnockoutGateConfig,
    V031KnockoutSummary,
    evaluate_v031_knockout_gate,
    make_v031_neutral_knockout_world,
)


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def test_v031_knockout_world_preserves_baseline_and_effort_geometry():
    world = make_v031_neutral_knockout_world()
    reference = world.fitting_model
    knocked = world.generating_model
    assert world.truth == 0.0
    assert world.generating_theta == {"sp": {"intercept": 2.0}}

    ref_fields = reference.latent_fields(
        {"sp": {"intercept": 2.0, "beta_x": 0.0}},
        world.covariates,
    )
    ko_fields = knocked.latent_fields(world.generating_theta, world.covariates)
    assert tuple(ref_fields.log_intensity["sp"].values()) == pytest.approx(
        tuple(ko_fields.log_intensity["sp"].values())
    )
    ref_effort = tuple(reference.streams[0].effort.at(key) for key in reference.domain.keys)
    ko_effort = tuple(knocked.streams[0].effort.at(key) for key in knocked.domain.keys)
    assert ref_effort == ko_effort
    assert len(set(round(value, 12) for value in ko_fields.log_intensity["sp"].values())) == 1
    assert next(iter(ko_fields.log_intensity["sp"].values())) == pytest.approx(2.0)


def test_v031_knockout_gate_mechanically_applies_frozen_thresholds():
    cfg = V031KnockoutGateConfig(replicates=100)
    passing = V031KnockoutSummary(
        replicates=100,
        mean_posterior=0.01,
        zero_coverage=0.90,
        nonzero_rate=0.08,
        total_divergences=0,
    )
    decision = evaluate_v031_knockout_gate(passing, config=cfg)
    assert decision.passed

    failing = V031KnockoutSummary(
        replicates=100,
        mean_posterior=0.25,
        zero_coverage=0.70,
        nonzero_rate=0.30,
        total_divergences=0,
    )
    assert not evaluate_v031_knockout_gate(failing, config=cfg).passed


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_v031_knockout_runner_smoke_uses_new_neutral_world():
    from esdm.validate.v031_knockout import run_v031_knockout_benchmark

    result = run_v031_knockout_benchmark(
        replicates=2,
        base_seed=73,
        num_warmup=40,
        num_samples=60,
        num_chains=1,
        progress_bar=False,
    )
    assert result.summary.replicates == 2
    assert math.isfinite(result.summary.mean_posterior)
    assert len(result.replicates) == 2
