"""Independent-seed v0.5f interaction transfer replication."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.simulate import simulate_observations
from .evidence import compare_knockout
from .v04_r2_run import _quantile, _subset_data
from .v05a_directed import (
    V05A_TARGET,
    V05A_WORLDS,
    build_v05a_fixture,
    v05a_theta,
)
from .v05a_run import (
    V05AReplicate,
    V05ASummary,
    _subset_model,
    summarize_v05a,
)


@dataclass(frozen=True, slots=True)
class V05FReplicate:
    world: str
    replicate: int
    truth_beta: float
    posterior_mean: float
    interval_low: float
    interval_high: float
    full_heldout_log_score: float
    partner_knockout_heldout_log_score: float
    full_divergences: int
    knockout_divergences: int

    def __post_init__(self) -> None:
        if self.world not in V05A_WORLDS:
            raise ValueError("unknown v0.5f world")
        for name, value in (
            ("full_heldout_log_score", self.full_heldout_log_score),
            ("partner_knockout_heldout_log_score", self.partner_knockout_heldout_log_score),
        ):
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")

    @property
    def heldout_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.partner_knockout_heldout_log_score)
        )

    @property
    def covers_truth(self) -> bool:
        return self.interval_low <= self.truth_beta <= self.interval_high

    @property
    def nonzero_interval(self) -> bool:
        return self.interval_low > 0.0 or self.interval_high < 0.0

    @property
    def positive_interval(self) -> bool:
        return self.interval_low > 0.0

    def as_v05a(self) -> V05AReplicate:
        return V05AReplicate(
            world=self.world,
            replicate=self.replicate,
            truth_beta=self.truth_beta,
            posterior_mean=self.posterior_mean,
            interval_low=self.interval_low,
            interval_high=self.interval_high,
            heldout_gain=self.heldout_gain,
            full_divergences=self.full_divergences,
            knockout_divergences=self.knockout_divergences,
        )


@dataclass(frozen=True, slots=True)
class V05FSummary:
    inherited_v05a: V05ASummary
    mean_full_heldout_log_score_by_world: dict
    mean_knockout_heldout_log_score_by_world: dict
    max_abs_gain_identity_error: float


def run_v05f_replicate(
    *,
    world: str,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V05FReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v05a_fixture()
    theta = v05a_theta(fixture, world)
    generated = simulate_observations(
        fixture.model,
        theta,
        fixture.covariates,
        theta_obs=fixture.theta_obs,
        seed=int(seed),
    )

    full_train, train_cov = _subset_model(
        fixture, fixture.train_spaces, knockout=False
    )
    knockout_train, knockout_train_cov = _subset_model(
        fixture, fixture.train_spaces, knockout=True
    )
    full_heldout, heldout_cov = _subset_model(
        fixture, fixture.heldout_spaces, knockout=False
    )
    knockout_heldout, knockout_heldout_cov = _subset_model(
        fixture, fixture.heldout_spaces, knockout=True
    )
    train_data = _subset_data(generated.counts, full_train)
    knockout_train_data = _subset_data(generated.counts, knockout_train)
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
        train_cov,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    knockout_fit = fit_numpyro(
        knockout_train,
        knockout_train_data,
        knockout_train_cov,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    draws = tuple(float(value) for value in full_fit.samples[V05A_TARGET])
    alpha = (1.0 - float(credible_mass)) / 2.0
    posterior_mean = math.fsum(draws) / len(draws)

    evidence = compare_knockout(
        full_heldout,
        full_fit.samples,
        knockout_heldout,
        knockout_fit.samples,
        full_covariates=heldout_cov,
        knockout_covariates=knockout_heldout_cov,
        data=heldout_data,
        stream_name="focal_records",
        species="focal",
    )
    if not math.isclose(
        float(evidence.full_log_score) - float(evidence.knockout_log_score),
        float(evidence.gain),
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise AssertionError("v0.5f knockout evidence score identity failed")

    return V05FReplicate(
        world=str(world),
        replicate=int(replicate),
        truth_beta=float(theta["focal"]["beta_partner"]),
        posterior_mean=posterior_mean,
        interval_low=_quantile(draws, alpha),
        interval_high=_quantile(draws, 1.0 - alpha),
        full_heldout_log_score=float(evidence.full_log_score),
        partner_knockout_heldout_log_score=float(evidence.knockout_log_score),
        full_divergences=int(full_fit.num_divergences),
        knockout_divergences=int(knockout_fit.num_divergences),
    )


def summarize_v05f(records: Sequence[V05FReplicate]) -> V05FSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.5f records must be non-empty")

    inherited = summarize_v05a(tuple(row.as_v05a() for row in rows))
    full_means = {}
    knockout_means = {}
    max_identity_error = 0.0

    for world in V05A_WORLDS:
        local = tuple(row for row in rows if row.world == world)
        if not local:
            raise ValueError("v0.5f summary requires both inherited v0.5a worlds")
        full_means[world] = math.fsum(
            float(row.full_heldout_log_score) for row in local
        ) / len(local)
        knockout_means[world] = math.fsum(
            float(row.partner_knockout_heldout_log_score) for row in local
        ) / len(local)
        for row in local:
            reconstructed = (
                float(row.full_heldout_log_score)
                - float(row.partner_knockout_heldout_log_score)
            )
            max_identity_error = max(
                max_identity_error,
                abs(reconstructed - float(row.heldout_gain)),
            )

    return V05FSummary(
        inherited_v05a=inherited,
        mean_full_heldout_log_score_by_world=full_means,
        mean_knockout_heldout_log_score_by_world=knockout_means,
        max_abs_gain_identity_error=max_identity_error,
    )
