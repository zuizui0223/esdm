"""Local structural-identification diagnostics from observation-rate sensitivities.

The diagnostic asks whether the target parameter contributes a sensitivity direction
that cannot be reproduced by the remaining free parameters. It is a local design check,
not a claim of scientific support and not a substitute for posterior/SBC diagnostics.
"""

from __future__ import annotations

import math

from .contraction import IdentificationResult, IdentificationStatus


def _parameter_sites(model):
    sites: list[tuple[str, str, str, str]] = []
    for species, processes in model.species.items():
        for process in processes:
            for parameter in process.priors():
                sites.append(
                    (f"{species}.{process.name}.{parameter}", "ecological", species, parameter)
                )
    for stream in model.streams:
        for parameter in getattr(stream, "priors", lambda: {})():
            sites.append(
                (f"stream.{stream.name}.{parameter}", "observation", stream.name, parameter)
            )
    return tuple(sites)


def _copy_nested(values):
    return {key: dict(block) for key, block in values.items()}


def _log_rate_vector(model, covariates, theta, theta_obs):
    fields = model.latent_fields(theta, covariates)
    values: list[float] = []
    for stream in model.streams:
        stream_theta = dict(theta_obs.get(stream.name, {}))
        for species in model.stream_targets(stream):
            rates = stream.expected_rates(
                species,
                fields,
                theta_obs=stream_theta,
                covariates=covariates,
            )
            for key in model.domain.keys:
                rate = float(rates[key])
                if not math.isfinite(rate) or rate <= 0.0:
                    raise ValueError(
                        "structural identification requires finite positive expected rates"
                    )
                values.append(math.log(rate))
    return tuple(values)


def _matrix_rank(matrix, *, tolerance: float) -> int:
    if not matrix:
        return 0
    rows = [list(map(float, row)) for row in matrix]
    n_rows = len(rows)
    n_cols = len(rows[0]) if rows else 0
    if any(len(row) != n_cols for row in rows):
        raise ValueError("matrix rows must have equal length")
    rank = 0
    pivot_col = 0
    while rank < n_rows and pivot_col < n_cols:
        pivot = max(range(rank, n_rows), key=lambda i: abs(rows[i][pivot_col]))
        if abs(rows[pivot][pivot_col]) <= tolerance:
            pivot_col += 1
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        pivot_value = rows[rank][pivot_col]
        rows[rank] = [value / pivot_value for value in rows[rank]]
        for i in range(n_rows):
            if i == rank:
                continue
            factor = rows[i][pivot_col]
            if abs(factor) <= tolerance:
                continue
            rows[i] = [
                rows[i][j] - factor * rows[rank][j]
                for j in range(n_cols)
            ]
        rank += 1
        pivot_col += 1
    return rank


def identify_parameter_from_design(
    model,
    covariates,
    *,
    theta,
    theta_obs=None,
    target: str,
    step: float = 1e-5,
    tolerance: float = 1e-7,
) -> IdentificationResult:
    """Classify local structural identification for one free parameter.

    A target is locally identified when its sensitivity column increases the rank of the
    full observation-rate sensitivity matrix relative to the matrix without that column.
    A zero sensitivity is `DesignUninformed`; a nonzero but redundant sensitivity is
    `NotIdentified`.
    """

    model.check_design()
    sites = _parameter_sites(model)
    site_names = tuple(site for site, *_ in sites)
    target_name = str(target)
    if target_name not in site_names:
        return IdentificationResult(
            status=IdentificationStatus.DESIGN_UNINFORMED,
            target=target_name,
            evidence=("target is not a declared free parameter",),
        )
    delta = float(step)
    if not math.isfinite(delta) or delta <= 0.0:
        raise ValueError("step must be finite and positive")
    tol = float(tolerance)
    if not math.isfinite(tol) or tol <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    obs = {} if theta_obs is None else _copy_nested(theta_obs)
    base_theta = _copy_nested(theta)
    base = _log_rate_vector(model, covariates, base_theta, obs)
    columns: list[tuple[float, ...]] = []

    for _site, kind, block_name, parameter in sites:
        perturbed_theta = _copy_nested(base_theta)
        perturbed_obs = _copy_nested(obs)
        if kind == "ecological":
            if block_name not in perturbed_theta or parameter not in perturbed_theta[block_name]:
                raise KeyError(f"missing nominal ecological parameter {block_name}:{parameter}")
            perturbed_theta[block_name][parameter] = (
                perturbed_theta[block_name][parameter] + delta
            )
        else:
            if block_name not in perturbed_obs or parameter not in perturbed_obs[block_name]:
                raise KeyError(f"missing nominal observation parameter {block_name}:{parameter}")
            perturbed_obs[block_name][parameter] = (
                perturbed_obs[block_name][parameter] + delta
            )
        shifted = _log_rate_vector(
            model,
            covariates,
            perturbed_theta,
            perturbed_obs,
        )
        columns.append(
            tuple((shifted[i] - base[i]) / delta for i in range(len(base)))
        )

    target_index = site_names.index(target_name)
    target_column = columns[target_index]
    if max(abs(value) for value in target_column) <= tol:
        return IdentificationResult(
            status=IdentificationStatus.DESIGN_UNINFORMED,
            target=target_name,
            evidence=("target has zero local sensitivity in all declared observations",),
        )

    # Convert column storage to conventional rows x parameters matrix.
    full_matrix = [
        [columns[j][i] for j in range(len(columns))]
        for i in range(len(base))
    ]
    reduced_matrix = [
        [columns[j][i] for j in range(len(columns)) if j != target_index]
        for i in range(len(base))
    ]
    full_rank = _matrix_rank(full_matrix, tolerance=tol)
    reduced_rank = _matrix_rank(reduced_matrix, tolerance=tol)
    status = (
        IdentificationStatus.IDENTIFIED
        if full_rank > reduced_rank
        else IdentificationStatus.NOT_IDENTIFIED
    )
    return IdentificationResult(
        status=status,
        target=target_name,
        evidence=(
            f"local_sensitivity_rank_full={full_rank}",
            f"local_sensitivity_rank_without_target={reduced_rank}",
            f"free_parameter_count={len(columns)}",
            f"observation_dimension={len(base)}",
        ),
    )
