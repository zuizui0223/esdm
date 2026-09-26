"""Replicated recovery/transfer runner for the qualified v0.4-R5 design."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.simulate import simulate_observations
from .v04_r2_run import (
    V04R2Replicate,
    _extrapolation_integrity,
    _posterior_intervals,
    _state_block_log_predictive_density,
    _subset_data,
    _subset_model,
    summarize_v04_r2,
)
from .v04_r5a_design import build_v04_r5a_fixture
from .v04_r5a_gate import evaluate_v04_r5a_identification


@dataclass(frozen=True, slots=True)
class V04R5BResult:
    replicates: tuple[V04R2Replicate, ...]
    summary: object
    train_space_count: int
    heldout_space_count: int
    annotated_space_count: int
    annotated_time_count: int
    state_calibration_context_count: int


def run_v04_r5b_replicate(
    source_csv_text: str,
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V04R2Replicate:
    """Run one frozen R5b full/reduced-model replicate."""

    from esdm.model.backend_numpyro import fit_numpyro

    mass = float(credible_mass)
    if not 0.0 < mass < 1.0:
        raise ValueError("credible_mass must be in (0, 1)")
    alpha = (1.0 - mass) / 2.0
    fixture = build_v04_r5a_fixture(source_csv_text)

    full_train, train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout=None
    )
    activity_train, activity_train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout="activity"
    )
    state_train, state_train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout="state"
    )
    full_heldout, heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout=None
    )
    activity_heldout, activity_heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout="activity"
    )
    state_heldout, state_heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout="state"
    )

    generated = simulate_observations(
        fixture.model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    train_data = _subset_data(generated.counts, full_train)
    heldout_data = _subset_data(generated.counts, full_heldout)

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    full_fit = fit_numpyro(
        full_train,
        train_data,
        train_covariates,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    activity_fit = fit_numpyro(
        activity_train,
        train_data,
        activity_train_covariates,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )
    state_fit = fit_numpyro(
        state_train,
        train_data,
        state_train_covariates,
        rng_seed=int(seed) + 3,
        **fit_kwargs,
    )

    means, lows, highs = _posterior_intervals(full_fit.samples, alpha)
    full_score = _state_block_log_predictive_density(
        full_heldout,
        full_fit.samples,
        heldout_covariates,
        heldout_data,
    )
    activity_score = _state_block_log_predictive_density(
        activity_heldout,
        activity_fit.samples,
        activity_heldout_covariates,
        heldout_data,
    )
    state_score = _state_block_log_predictive_density(
        state_heldout,
        state_fit.samples,
        state_heldout_covariates,
        heldout_data,
    )
    return V04R2Replicate(
        replicate=int(replicate),
        posterior_means=means,
        posterior_lows=lows,
        posterior_highs=highs,
        full_heldout_log_score=full_score,
        activity_knockout_heldout_log_score=activity_score,
        state_knockout_heldout_log_score=state_score,
        full_divergences=full_fit.num_divergences,
        activity_knockout_divergences=activity_fit.num_divergences,
        state_knockout_divergences=state_fit.num_divergences,
    )


def summarize_v04_r5b(source_csv_text: str, records):
    """Summarize R5b records using the unchanged R2 recovery/transfer contract."""

    fixture = build_v04_r5a_fixture(source_csv_text)
    identification = evaluate_v04_r5a_identification(source_csv_text)
    return summarize_v04_r2(
        tuple(records),
        identification=identification,
        extrapolation_integrity=_extrapolation_integrity(fixture),
    )
