"""Replicated hidden-common-driver stress test for v0.5b."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .evidence import compare_knockout
from .v04_r2_run import _quantile, _subset_data
from .v05b_hidden_driver import V05B_TARGET, build_v05b_fixture


@dataclass(frozen=True, slots=True)
class V05BReplicate:
    replicate: int
    posterior_mean: float
    interval_low: float
    interval_high: float
    heldout_gain: float
    full_divergences: int
    knockout_divergences: int

    @property
    def covers_zero(self) -> bool:
        return self.interval_low <= 0.0 <= self.interval_high

    @property
    def nonzero_interval(self) -> bool:
        return self.interval_low > 0.0 or self.interval_high < 0.0

    @property
    def positive_interval(self) -> bool:
        return self.interval_low > 0.0


@dataclass(frozen=True, slots=True)
class V05BSummary:
    replicates: int
    fit_count: int
    mean_beta: float
    zero_coverage: float
    nonzero_interval_rate: float
    positive_interval_rate: float
    heldout_positive_gain_rate: float
    heldout_material_gain_rate: float
    mean_heldout_gain: float
    total_divergences: int


def _subset_model(fixture, spaces, *, knockout: bool):
    grid = Grid(
        space=tuple(spaces),
        doy=fixture.fitting_model.domain.doy,
        hour=fixture.fitting_model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.fitting_model.species,
        streams=fixture.fitting_model.streams,
    )
    if knockout:
        model = model.knockout("focal", "partner_effect")
    covariates = {
        key: dict(fixture.fitting_covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def run_v05b_replicate(
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V05BReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v05b_fixture()
    generated = simulate_observations(
        fixture.generating_model,
        fixture.generating_theta,
        fixture.generating_covariates,
        theta_obs=fixture.theta_obs,
        seed=int(seed),
    )

    full_train, train_cov = _subset_model(
        fixture, fixture.train_spaces, knockout=False
    )
    knockout_train, knockout_cov = _subset_model(
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
        knockout_cov,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    draws = tuple(float(value) for value in full_fit.samples[V05B_TARGET])
    alpha = (1.0 - float(credible_mass)) / 2.0
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
    return V05BReplicate(
        replicate=int(replicate),
        posterior_mean=math.fsum(draws) / len(draws),
        interval_low=_quantile(draws, alpha),
        interval_high=_quantile(draws, 1.0 - alpha),
        heldout_gain=float(evidence.gain),
        full_divergences=full_fit.num_divergences,
        knockout_divergences=knockout_fit.num_divergences,
    )


def summarize_v05b(
    records: Sequence[V05BReplicate],
    *,
    material_gain_threshold: float = 0.005,
) -> V05BSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.5b records must be non-empty")
    n = len(rows)
    return V05BSummary(
        replicates=n,
        fit_count=2 * n,
        mean_beta=math.fsum(row.posterior_mean for row in rows) / n,
        zero_coverage=sum(row.covers_zero for row in rows) / n,
        nonzero_interval_rate=sum(row.nonzero_interval for row in rows) / n,
        positive_interval_rate=sum(row.positive_interval for row in rows) / n,
        heldout_positive_gain_rate=sum(
            row.heldout_gain > 0.0 for row in rows
        ) / n,
        heldout_material_gain_rate=sum(
            row.heldout_gain > float(material_gain_threshold)
            for row in rows
        ) / n,
        mean_heldout_gain=math.fsum(row.heldout_gain for row in rows) / n,
        total_divergences=sum(
            int(row.full_divergences) + int(row.knockout_divergences)
            for row in rows
        ),
    )
