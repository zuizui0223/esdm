"""Replicated budget-matched calibration comparison for v0.4-R7."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
import math

from esdm.simulate import simulate_observations
from .v04_r2_gate import R2_RECOVERY_TRUTH
from .v04_r2_run import (
    _state_block_log_predictive_density,
    _subset_data,
    _subset_model,
)
from .v04_r7_design import (
    R7_EXPECTED_LABEL_BUDGET,
    build_v04_r7_direct_fixture,
    build_v04_r7_passive_fixture,
    expected_direct_labels,
)


R7_STATE_TARGETS = tuple(
    target
    for target in R2_RECOVERY_TRUTH
    if target.startswith("sp.state.")
)


@dataclass(frozen=True, slots=True)
class V04R7Replicate:
    replicate: int
    seed: int
    shared_base_data_equal: bool
    direct_expected_labels: float
    passive_expected_labels: float
    direct_realized_labels: int
    passive_realized_labels: int
    direct_heldout_log_score: float
    passive_heldout_log_score: float
    direct_state_mean_abs_error: float
    passive_state_mean_abs_error: float
    direct_divergences: int
    passive_divergences: int

    @property
    def heldout_gain(self) -> float:
        return (
            float(self.direct_heldout_log_score)
            - float(self.passive_heldout_log_score)
        )

    @property
    def state_error_gain(self) -> float:
        return (
            float(self.passive_state_mean_abs_error)
            - float(self.direct_state_mean_abs_error)
        )


@dataclass(frozen=True, slots=True)
class V04R7Summary:
    replicates: int
    fit_count: int
    all_shared_base_data_equal: bool
    direct_expected_labels: float
    passive_expected_labels: float
    mean_direct_realized_labels: float
    mean_passive_realized_labels: float
    heldout_positive_gain_rate: float
    mean_heldout_gain: float
    state_error_positive_gain_rate: float
    mean_state_error_gain: float
    total_divergences: int


def _posterior_state_error(samples, truth) -> float:
    errors = []
    for target in R7_STATE_TARGETS:
        parameter = target.split(".")[-1]
        draws = tuple(float(value) for value in samples[target])
        mean = math.fsum(draws) / len(draws)
        errors.append(abs(mean - float(truth["sp"][parameter])))
    return math.fsum(errors) / len(errors)


def _realized_state_labels(generated, stream_name: str) -> int:
    by_state = generated.counts[stream_name]["sp"]
    return sum(
        int(value)
        for state_counts in by_state.values()
        for value in state_counts.values()
    )


def _base_stream_counts(generated):
    return {
        name: generated.counts[name]
        for name in ("opportunistic", "calibrated", "annotated")
    }


def run_v04_r7_replicate(
    source_csv_text: str,
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V04R7Replicate:
    from esdm.model.backend_numpyro import fit_numpyro

    direct = build_v04_r7_direct_fixture(source_csv_text)
    passive = build_v04_r7_passive_fixture(source_csv_text)

    generated_direct = simulate_observations(
        direct.model,
        direct.generating_theta,
        direct.covariates,
        theta_obs=direct.generating_theta_obs,
        seed=int(seed),
    )
    generated_passive = simulate_observations(
        passive.model,
        passive.generating_theta,
        passive.covariates,
        theta_obs=passive.generating_theta_obs,
        seed=int(seed),
    )
    shared_equal = _base_stream_counts(generated_direct) == _base_stream_counts(
        generated_passive
    )
    if not shared_equal:
        raise RuntimeError("R7 paired designs do not share identical base observations")

    direct_train, direct_cov = _subset_model(
        direct, direct.train_spaces, knockout=None
    )
    passive_train, passive_cov = _subset_model(
        passive, passive.train_spaces, knockout=None
    )
    direct_heldout, direct_heldout_cov = _subset_model(
        direct, direct.heldout_spaces, knockout=None
    )
    passive_heldout, passive_heldout_cov = _subset_model(
        passive, passive.heldout_spaces, knockout=None
    )

    direct_train_data = _subset_data(generated_direct.counts, direct_train)
    passive_train_data = _subset_data(generated_passive.counts, passive_train)
    heldout_data = _subset_data(generated_direct.counts, direct_heldout)

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    direct_fit = fit_numpyro(
        direct_train,
        direct_train_data,
        direct_cov,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    passive_fit = fit_numpyro(
        passive_train,
        passive_train_data,
        passive_cov,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    direct_score = _state_block_log_predictive_density(
        direct_heldout,
        direct_fit.samples,
        direct_heldout_cov,
        heldout_data,
    )
    passive_score = _state_block_log_predictive_density(
        passive_heldout,
        passive_fit.samples,
        passive_heldout_cov,
        heldout_data,
    )

    return V04R7Replicate(
        replicate=int(replicate),
        seed=int(seed),
        shared_base_data_equal=True,
        direct_expected_labels=expected_direct_labels(source_csv_text),
        passive_expected_labels=passive.expected_passive_labels,
        direct_realized_labels=_realized_state_labels(
            generated_direct, "state_calibration"
        ),
        passive_realized_labels=_realized_state_labels(
            generated_passive, "passive_calibration"
        ),
        direct_heldout_log_score=direct_score,
        passive_heldout_log_score=passive_score,
        direct_state_mean_abs_error=_posterior_state_error(
            direct_fit.samples, direct.generating_theta
        ),
        passive_state_mean_abs_error=_posterior_state_error(
            passive_fit.samples, passive.generating_theta
        ),
        direct_divergences=direct_fit.num_divergences,
        passive_divergences=passive_fit.num_divergences,
    )


def summarize_v04_r7(records: Sequence[V04R7Replicate]) -> V04R7Summary:
    rows = tuple(records)
    if not rows:
        raise ValueError("R7 records must be non-empty")
    return V04R7Summary(
        replicates=len(rows),
        fit_count=2 * len(rows),
        all_shared_base_data_equal=all(row.shared_base_data_equal for row in rows),
        direct_expected_labels=rows[0].direct_expected_labels,
        passive_expected_labels=rows[0].passive_expected_labels,
        mean_direct_realized_labels=math.fsum(
            row.direct_realized_labels for row in rows
        ) / len(rows),
        mean_passive_realized_labels=math.fsum(
            row.passive_realized_labels for row in rows
        ) / len(rows),
        heldout_positive_gain_rate=sum(
            row.heldout_gain > 0.0 for row in rows
        ) / len(rows),
        mean_heldout_gain=math.fsum(
            row.heldout_gain for row in rows
        ) / len(rows),
        state_error_positive_gain_rate=sum(
            row.state_error_gain > 0.0 for row in rows
        ) / len(rows),
        mean_state_error_gain=math.fsum(
            row.state_error_gain for row in rows
        ) / len(rows),
        total_divergences=sum(
            int(row.direct_divergences) + int(row.passive_divergences)
            for row in rows
        ),
    )
