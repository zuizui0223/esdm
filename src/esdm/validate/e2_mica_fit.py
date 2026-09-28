"""Frozen fitting and row-level held-out scoring for E2 MICA."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping

from esdm.domain import Grid
from esdm.model import Model

from .e2_mica_full_response import E2MicaEmpiricalFixture
from .empirical_snapshot_japan_fit import _parameter_summaries


FROZEN_NUM_WARMUP = 300
FROZEN_NUM_SAMPLES = 350
FROZEN_NUM_CHAINS = 2
FROZEN_TARGET_ACCEPT = 0.90
FROZEN_RNG_SEED_FULL = 20260927
FROZEN_RNG_SEED_ACTIVITY = 20260928
FROZEN_RNG_SEED_STATE = 20260929
ODSP_AGGREGATE_TOLERANCE = 1e-12


@dataclass(frozen=True, slots=True)
class E2MicaFitResult:
    parameter_summaries: Mapping[str, Mapping[str, float]]
    full_heldout_log_score: float
    activity_knockout_heldout_log_score: float
    state_knockout_heldout_log_score: float
    full_divergences: int
    activity_knockout_divergences: int
    state_knockout_divergences: int
    heldout_deployment_scores: tuple[Mapping[str, object], ...]

    @property
    def activity_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.activity_knockout_heldout_log_score)
        )

    @property
    def state_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.state_knockout_heldout_log_score)
        )

    @property
    def total_divergences(self) -> int:
        return (
            int(self.full_divergences)
            + int(self.activity_knockout_divergences)
            + int(self.state_knockout_divergences)
        )

    @property
    def sampling_passed(self) -> bool:
        scores = (
            self.full_heldout_log_score,
            self.activity_knockout_heldout_log_score,
            self.state_knockout_heldout_log_score,
        )
        return (
            self.total_divergences == 0
            and all(math.isfinite(float(value)) for value in scores)
        )


def _subset_model(
    fixture: E2MicaEmpiricalFixture,
    spaces,
    *,
    knockout: str | None,
):
    grid = Grid(
        space=tuple(str(space) for space in spaces),
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.model.species,
        streams=fixture.model.streams,
    )
    if knockout is not None:
        if knockout not in {"activity", "state"}:
            raise ValueError("knockout must be None, 'activity', or 'state'")
        model = model.knockout("sp", knockout)
    covariates = {
        key: fixture.covariates[key]
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def _subset_sparse_data(
    fixture: E2MicaEmpiricalFixture,
    model: Model,
):
    allowed = set(model.domain.keys)
    output = {}
    for stream in model.streams:
        output[stream.name] = {}
        for species in model.stream_targets(stream):
            source = fixture.data[stream.name][species]
            state_space = getattr(stream, "state_space", None)
            if state_space is None:
                output[stream.name][species] = {
                    key: int(value)
                    for key, value in source.items()
                    if key in allowed
                }
            else:
                output[stream.name][species] = {
                    state: {
                        key: int(value)
                        for key, value in source[state].items()
                        if key in allowed
                    }
                    for state in state_space.states
                }
    return output


def _streaming_logmeanexp_update(
    running_max,
    running_sum,
    values,
):
    import numpy as np

    chunk_max = np.max(values, axis=0)
    new_max = np.maximum(running_max, chunk_max)
    prior_term = np.where(
        np.isfinite(running_max),
        running_sum * np.exp(running_max - new_max),
        0.0,
    )
    chunk_term = np.sum(np.exp(values - new_max[None, :]), axis=0)
    return new_max, prior_term + chunk_term


def _annotated_deployment_scores(
    model: Model,
    samples,
    covariates,
    data,
    *,
    chunk_size: int = 25,
):
    """Score active held-out annotated cells and return equal-weight deployment rows."""

    import jax
    import jax.numpy as jnp
    import numpy as np

    from esdm.model.backend_numpyro import _parameter_layout

    annotated = tuple(
        stream for stream in model.streams if stream.name == "annotated"
    )
    if len(annotated) != 1:
        raise ValueError("E2 MICA heldout model must contain one annotated stream")
    stream = annotated[0]
    ordered_keys = tuple(model.domain.keys)
    mask = tuple(stream.structural_exposure_mask(ordered_keys))
    exposed_indices = tuple(
        index for index, exposed in enumerate(mask) if exposed
    )
    if not exposed_indices:
        raise ValueError("E2 MICA heldout annotated stream has no scored cells")

    states = tuple(stream.state_space.states)
    if states != ("solitary", "group"):
        raise ValueError("E2 MICA heldout state labels drifted")
    counts_by_state = data["annotated"]["sp"]
    counts = []
    deployments = []
    for state in states:
        for index in exposed_indices:
            key = ordered_keys[index]
            counts.append(int(counts_by_state[state].get(key, 0)))
            deployments.append(str(key[0]))
    count_array = np.asarray(counts, dtype=np.int64)
    if np.any(count_array < 0):
        raise ValueError("E2 MICA heldout counts must be non-negative")

    ecological_layout = tuple(_parameter_layout(model))
    sites = tuple(site for site, *_rest in ecological_layout)
    missing = [site for site in sites if site not in samples]
    if missing:
        raise KeyError(f"E2 MICA posterior samples missing sites: {missing[:3]!r}")
    draw_counts = {len(samples[site]) for site in sites}
    if len(draw_counts) != 1:
        raise ValueError("E2 MICA posterior ecological sample lengths differ")
    n_draws = draw_counts.pop()
    if n_draws < 1:
        raise ValueError("E2 MICA heldout scoring requires posterior draws")

    index_array = jnp.asarray(exposed_indices, dtype=jnp.int32)

    def rates_for_draw(*parameter_values):
        theta = {species: {} for species in model.species}
        for value, (_site, species, parameter, _prior) in zip(
            parameter_values,
            ecological_layout,
            strict=True,
        ):
            theta[species][parameter] = value
        fields = model.latent_field_arrays(
            theta,
            covariates,
            array_module=jnp,
        )
        blocks = stream.observation_blocks(
            "sp",
            fields,
            data=None,
            theta_obs={},
            covariates=covariates,
            array_module=jnp,
        )
        if tuple(block.name for block in blocks) != (
            "annotated.sp.solitary",
            "annotated.sp.group",
        ):
            raise ValueError("E2 MICA annotated block order drifted")
        return jnp.concatenate(
            [
                jnp.asarray(block.rates)[index_array]
                for block in blocks
            ],
            axis=0,
        )

    batched = jax.jit(jax.vmap(rates_for_draw))
    cell_count = len(count_array)
    running_max = np.full(cell_count, -np.inf, dtype=np.float64)
    running_sum = np.zeros(cell_count, dtype=np.float64)
    seen_draws = 0
    lgamma = np.asarray(
        [math.lgamma(int(value) + 1.0) for value in count_array],
        dtype=np.float64,
    )

    for start in range(0, n_draws, int(chunk_size)):
        end = min(n_draws, start + int(chunk_size))
        arguments = [
            jnp.asarray(samples[site][start:end])
            for site in sites
        ]
        rates = np.asarray(batched(*arguments), dtype=np.float64)
        if rates.shape != (end - start, cell_count):
            raise RuntimeError(
                f"E2 MICA heldout rate shape drift: {rates.shape}"
            )
        positive = rates > 0.0
        safe_rates = np.where(positive, rates, 1.0)
        log_mass = (
            count_array[None, :] * np.log(safe_rates)
            - rates
            - lgamma[None, :]
        )
        impossible = (~positive) & (count_array[None, :] > 0)
        log_mass = np.where(
            impossible,
            -np.inf,
            np.where(positive, log_mass, 0.0),
        )
        running_max, running_sum = _streaming_logmeanexp_update(
            running_max,
            running_sum,
            log_mass,
        )
        seen_draws += end - start

    if seen_draws != n_draws:
        raise RuntimeError("E2 MICA heldout posterior draw count drift")
    with np.errstate(divide="ignore", invalid="ignore"):
        cell_scores = running_max + np.log(running_sum / n_draws)
    all_impossible = ~np.isfinite(running_max)
    cell_scores[all_impossible] = -np.inf

    positions_by_deployment = {}
    for index, deployment_id in enumerate(deployments):
        positions_by_deployment.setdefault(deployment_id, []).append(index)

    expected_deployments = tuple(sorted(model.domain.space))
    if set(positions_by_deployment) != set(expected_deployments):
        missing_deployments = sorted(
            set(expected_deployments) - set(positions_by_deployment)
        )
        raise ValueError(
            "E2 MICA heldout deployment lacks scored state cells: "
            f"{missing_deployments[:3]!r}"
        )

    rows = []
    for deployment_id in expected_deployments:
        positions = positions_by_deployment[deployment_id]
        values = [float(cell_scores[index]) for index in positions]
        score = math.fsum(values) / len(values)
        rows.append({
            "deploymentID": deployment_id,
            "score": score,
            "scored_state_context_cells": len(values),
        })
    aggregate = math.fsum(float(row["score"]) for row in rows) / len(rows)
    return aggregate, tuple(rows)


def _combine_deployment_scores(full_rows, activity_rows, state_rows):
    full = {row["deploymentID"]: row for row in full_rows}
    activity = {row["deploymentID"]: row for row in activity_rows}
    state = {row["deploymentID"]: row for row in state_rows}
    if not (set(full) == set(activity) == set(state)):
        raise ValueError("E2 MICA heldout deployment row sets differ across models")

    output = []
    for deployment_id in sorted(full):
        cell_counts = {
            int(full[deployment_id]["scored_state_context_cells"]),
            int(activity[deployment_id]["scored_state_context_cells"]),
            int(state[deployment_id]["scored_state_context_cells"]),
        }
        if len(cell_counts) != 1:
            raise ValueError("E2 MICA scored heldout cell counts differ across models")
        output.append({
            "deploymentID": deployment_id,
            "full_heldout_log_score": float(full[deployment_id]["score"]),
            "activity_knockout_heldout_log_score": float(
                activity[deployment_id]["score"]
            ),
            "state_knockout_heldout_log_score": float(
                state[deployment_id]["score"]
            ),
            "scored_state_context_cells": cell_counts.pop(),
        })
    return tuple(output)


def _assert_aggregate_consistency(rows, field, aggregate):
    observed = math.fsum(float(row[field]) for row in rows) / len(rows)
    if not math.isclose(
        observed,
        float(aggregate),
        rel_tol=0.0,
        abs_tol=ODSP_AGGREGATE_TOLERANCE,
    ):
        raise RuntimeError(
            f"E2 MICA ODSP aggregate mismatch for {field}: "
            f"{observed} != {aggregate}"
        )


def fit_e2_mica_empirical(
    fixture: E2MicaEmpiricalFixture,
    *,
    progress_bar: bool = False,
) -> E2MicaFitResult:
    """Run the frozen full/activity-knockout/state-knockout E2 endpoint."""

    from esdm.model.backend_numpyro import fit_numpyro

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

    train_data = _subset_sparse_data(fixture, full_train)
    heldout_data = _subset_sparse_data(fixture, full_heldout)
    fit_kwargs = {
        "num_warmup": FROZEN_NUM_WARMUP,
        "num_samples": FROZEN_NUM_SAMPLES,
        "num_chains": FROZEN_NUM_CHAINS,
        "progress_bar": bool(progress_bar),
        "target_accept_prob": FROZEN_TARGET_ACCEPT,
    }
    full_fit = fit_numpyro(
        full_train,
        train_data,
        train_covariates,
        rng_seed=FROZEN_RNG_SEED_FULL,
        **fit_kwargs,
    )
    activity_fit = fit_numpyro(
        activity_train,
        train_data,
        activity_train_covariates,
        rng_seed=FROZEN_RNG_SEED_ACTIVITY,
        **fit_kwargs,
    )
    state_fit = fit_numpyro(
        state_train,
        train_data,
        state_train_covariates,
        rng_seed=FROZEN_RNG_SEED_STATE,
        **fit_kwargs,
    )

    full_score, full_rows = _annotated_deployment_scores(
        full_heldout,
        full_fit.samples,
        heldout_covariates,
        heldout_data,
    )
    activity_score, activity_rows = _annotated_deployment_scores(
        activity_heldout,
        activity_fit.samples,
        activity_heldout_covariates,
        heldout_data,
    )
    state_score, state_rows = _annotated_deployment_scores(
        state_heldout,
        state_fit.samples,
        state_heldout_covariates,
        heldout_data,
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

    return E2MicaFitResult(
        parameter_summaries=_parameter_summaries(full_fit.samples),
        full_heldout_log_score=full_score,
        activity_knockout_heldout_log_score=activity_score,
        state_knockout_heldout_log_score=state_score,
        full_divergences=full_fit.num_divergences,
        activity_knockout_divergences=activity_fit.num_divergences,
        state_knockout_divergences=state_fit.num_divergences,
        heldout_deployment_scores=rows,
    )
