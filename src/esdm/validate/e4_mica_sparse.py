"""Exact sparse-domain execution of the frozen E3 reduced MICA endpoint."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.model import (
    StructuralExposureCompaction,
    compact_model_by_structural_exposure,
)

from .e2_mica_fit import (
    E2MicaFitResult,
    FROZEN_NUM_CHAINS,
    FROZEN_NUM_SAMPLES,
    FROZEN_NUM_WARMUP,
    FROZEN_RNG_SEED_ACTIVITY,
    FROZEN_RNG_SEED_FULL,
    FROZEN_RNG_SEED_STATE,
    FROZEN_TARGET_ACCEPT,
    _annotated_deployment_scores,
    _assert_aggregate_consistency,
    _combine_deployment_scores,
    _parameter_summaries,
    _subset_model,
    _subset_sparse_data,
)
from .e2_mica_full_response import E2MicaEmpiricalFixture


@dataclass(frozen=True, slots=True)
class E4MicaSparsePrepared:
    training_model: object
    training_covariates: object
    training_data: object
    training_compaction: StructuralExposureCompaction
    heldout_model: object
    heldout_covariates: object
    heldout_data: object
    heldout_compaction: StructuralExposureCompaction


@dataclass(frozen=True, slots=True)
class E4MicaSparseFitResult:
    scientific_result: E2MicaFitResult
    training_compaction: StructuralExposureCompaction
    heldout_compaction: StructuralExposureCompaction

    @property
    def full_heldout_log_score(self) -> float:
        return self.scientific_result.full_heldout_log_score

    @property
    def activity_knockout_heldout_log_score(self) -> float:
        return self.scientific_result.activity_knockout_heldout_log_score

    @property
    def state_knockout_heldout_log_score(self) -> float:
        return self.scientific_result.state_knockout_heldout_log_score

    @property
    def activity_gain(self) -> float:
        return self.scientific_result.activity_gain

    @property
    def state_gain(self) -> float:
        return self.scientific_result.state_gain

    @property
    def total_divergences(self) -> int:
        return self.scientific_result.total_divergences

    @property
    def sampling_passed(self) -> bool:
        return self.scientific_result.sampling_passed


def prepare_e4_mica_sparse(
    fixture: E2MicaEmpiricalFixture,
) -> E4MicaSparsePrepared:
    """Build exact compact training and heldout domains without fitting."""

    dense_train, train_covariates = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout=None,
    )
    dense_heldout, heldout_covariates = _subset_model(
        fixture,
        fixture.heldout_spaces,
        knockout=None,
    )
    train_data = _subset_sparse_data(fixture, dense_train)
    heldout_data = _subset_sparse_data(fixture, dense_heldout)

    (
        sparse_train,
        sparse_train_covariates,
        sparse_train_data,
        train_report,
    ) = compact_model_by_structural_exposure(
        dense_train,
        train_covariates,
        train_data,
    )
    (
        sparse_heldout,
        sparse_heldout_covariates,
        sparse_heldout_data,
        heldout_report,
    ) = compact_model_by_structural_exposure(
        dense_heldout,
        heldout_covariates,
        heldout_data,
    )

    return E4MicaSparsePrepared(
        training_model=sparse_train,
        training_covariates=sparse_train_covariates,
        training_data=sparse_train_data,
        training_compaction=train_report,
        heldout_model=sparse_heldout,
        heldout_covariates=sparse_heldout_covariates,
        heldout_data=sparse_heldout_data,
        heldout_compaction=heldout_report,
    )


def fit_e4_mica_sparse_nuts(
    fixture: E2MicaEmpiricalFixture,
    *,
    progress_bar: bool = False,
) -> E4MicaSparseFitResult:
    """Fit the E3 scientific endpoint on an exactly compacted domain."""

    from esdm.model.backend_numpyro import fit_numpyro

    prepared = prepare_e4_mica_sparse(fixture)
    full_train = prepared.training_model
    activity_train = full_train.knockout("sp", "activity")
    state_train = full_train.knockout("sp", "state")
    full_heldout = prepared.heldout_model
    activity_heldout = full_heldout.knockout("sp", "activity")
    state_heldout = full_heldout.knockout("sp", "state")

    fit_kwargs = {
        "num_warmup": FROZEN_NUM_WARMUP,
        "num_samples": FROZEN_NUM_SAMPLES,
        "num_chains": FROZEN_NUM_CHAINS,
        "progress_bar": bool(progress_bar),
        "target_accept_prob": FROZEN_TARGET_ACCEPT,
    }
    full_fit = fit_numpyro(
        full_train,
        prepared.training_data,
        prepared.training_covariates,
        rng_seed=FROZEN_RNG_SEED_FULL,
        **fit_kwargs,
    )
    activity_fit = fit_numpyro(
        activity_train,
        prepared.training_data,
        prepared.training_covariates,
        rng_seed=FROZEN_RNG_SEED_ACTIVITY,
        **fit_kwargs,
    )
    state_fit = fit_numpyro(
        state_train,
        prepared.training_data,
        prepared.training_covariates,
        rng_seed=FROZEN_RNG_SEED_STATE,
        **fit_kwargs,
    )

    full_score, full_rows = _annotated_deployment_scores(
        full_heldout,
        full_fit.samples,
        prepared.heldout_covariates,
        prepared.heldout_data,
    )
    activity_score, activity_rows = _annotated_deployment_scores(
        activity_heldout,
        activity_fit.samples,
        prepared.heldout_covariates,
        prepared.heldout_data,
    )
    state_score, state_rows = _annotated_deployment_scores(
        state_heldout,
        state_fit.samples,
        prepared.heldout_covariates,
        prepared.heldout_data,
    )
    rows = _combine_deployment_scores(
        full_rows,
        activity_rows,
        state_rows,
    )
    _assert_aggregate_consistency(
        rows,
        "full_heldout_log_score",
        full_score,
    )
    _assert_aggregate_consistency(
        rows,
        "activity_knockout_heldout_log_score",
        activity_score,
    )
    _assert_aggregate_consistency(
        rows,
        "state_knockout_heldout_log_score",
        state_score,
    )

    scientific = E2MicaFitResult(
        parameter_summaries=_parameter_summaries(full_fit.samples),
        full_heldout_log_score=full_score,
        activity_knockout_heldout_log_score=activity_score,
        state_knockout_heldout_log_score=state_score,
        full_divergences=full_fit.num_divergences,
        activity_knockout_divergences=activity_fit.num_divergences,
        state_knockout_divergences=state_fit.num_divergences,
        heldout_deployment_scores=rows,
    )
    return E4MicaSparseFitResult(
        scientific_result=scientific,
        training_compaction=prepared.training_compaction,
        heldout_compaction=prepared.heldout_compaction,
    )
